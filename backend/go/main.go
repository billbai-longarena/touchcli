package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

// ============================================================================
// Configuration
// ============================================================================

const (
	AGENT_SERVICE_URL = "http://localhost:8000"
	GATEWAY_PORT      = "8080"
)

var (
	upgrader = websocket.Upgrader{
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
		CheckOrigin: func(r *http.Request) bool {
			// TODO: Implement proper CORS origin checking
			return true
		},
	}
)

// ============================================================================
// WebSocket Frame (from WEBSOCKET_SPEC.md)
// ============================================================================

type WebSocketFrame struct {
	Type           string          `json:"type"` // message, agent-action, agent-state, heartbeat, error
	ID             string          `json:"id"`
	ConversationID string          `json:"conversation_id"`
	Timestamp      time.Time       `json:"timestamp"`
	Payload        json.RawMessage `json:"payload"`
}

type Client struct {
	ID   string
	Conn *websocket.Conn
	Send chan []byte
}

type Hub struct {
	Clients    map[*Client]bool
	Broadcast  chan []byte
	Register   chan *Client
	Unregister chan *Client
}

// ============================================================================
// Hub Management
// ============================================================================

var hub = &Hub{
	Clients:    make(map[*Client]bool),
	Broadcast:  make(chan []byte, 256),
	Register:   make(chan *Client),
	Unregister: make(chan *Client),
}

func (h *Hub) run() {
	for {
		select {
		case client := <-h.Register:
			h.Clients[client] = true
			log.Printf("Client registered: %s (total: %d)", client.ID, len(h.Clients))

		case client := <-h.Unregister:
			if _, ok := h.Clients[client]; ok {
				delete(h.Clients, client)
				close(client.Send)
				log.Printf("Client unregistered: %s (total: %d)", client.ID, len(h.Clients))
			}

		case message := <-h.Broadcast:
			for client := range h.Clients {
				select {
				case client.Send <- message:
				default:
					// Client's send channel is full, skip
					close(client.Send)
					delete(h.Clients, client)
				}
			}
		}
	}
}

// ============================================================================
// Client Read/Write Pumps
// ============================================================================

func (c *Client) readPump() {
	defer func() {
		hub.Unregister <- c
		c.Conn.Close()
	}()

	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		var frame WebSocketFrame
		err := c.Conn.ReadJSON(&frame)
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("WebSocket error: %v", err)
			}
			break
		}

		log.Printf("Received frame: type=%s, conversation=%s", frame.Type, frame.ConversationID)

		// TODO: Forward frame to Python Agent Service
		// resp, err := http.Post(
		//     fmt.Sprintf("%s/api/v1/messages", AGENT_SERVICE_URL),
		//     "application/json",
		//     bytes.NewReader(frame.Payload),
		// )
	}
}

func (c *Client) writePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			if err := c.Conn.WriteMessage(websocket.TextMessage, message); err != nil {
				return
			}

		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			heartbeat := WebSocketFrame{
				Type:      "heartbeat",
				ID:        fmt.Sprintf("hb-%d", time.Now().Unix()),
				Timestamp: time.Now(),
				Payload:   json.RawMessage(`{"status":"ok"}`),
			}
			data, _ := json.Marshal(heartbeat)
			if err := c.Conn.WriteMessage(websocket.TextMessage, data); err != nil {
				return
			}
		}
	}
}

// ============================================================================
// Handlers
// ============================================================================

func handleWebSocket(c *gin.Context) {
	ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	client := &Client{
		ID:   fmt.Sprintf("client-%d", time.Now().UnixNano()),
		Conn: ws,
		Send: make(chan []byte, 256),
	}

	hub.Register <- client

	log.Printf("New WebSocket connection: %s", client.ID)

	go client.readPump()
	go client.writePump()
}

func healthCheck(c *gin.Context) {
	// TODO: Check backend service health
	agentServiceOk := checkServiceHealth(AGENT_SERVICE_URL)

	statusCode := "ok"
	if !agentServiceOk {
		statusCode = "degraded"
	}

	c.JSON(200, gin.H{
		"status":        statusCode,
		"agent_service": map[string]interface{}{"status": "ok" + fmt.Sprint(!agentServiceOk)},
	})
}

func checkServiceHealth(serviceURL string) bool {
	resp, err := http.Get(fmt.Sprintf("%s/health", serviceURL))
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == 200
}

func proxyRequest(c *gin.Context) {
	// Proxy HTTP requests to Python Agent Service
	target, err := url.Parse(AGENT_SERVICE_URL)
	if err != nil {
		c.JSON(500, gin.H{"error": "Invalid service URL"})
		return
	}

	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.Director = func(req *http.Request) {
		req.URL.Scheme = target.Scheme
		req.URL.Host = target.Host
		req.URL.Path = fmt.Sprintf("/api/v1%s", c.Request.URL.Path)
		req.Header.Set("X-Forwarded-For", c.ClientIP())
	}

	proxy.ServeHTTP(c.Writer, c.Request)
}

// ============================================================================
// Main
// ============================================================================

func main() {
	// Start hub
	go hub.run()

	// Set Gin mode
	gin.SetMode(gin.ReleaseMode)
	if os.Getenv("GIN_MODE") == "debug" {
		gin.SetMode(gin.DebugMode)
	}

	// Create router
	router := gin.Default()

	// CORS middleware
	router.Use(func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(204)
			return
		}

		c.Next()
	})

	// Routes
	router.GET("/health", healthCheck)
	router.GET("/ws", handleWebSocket)

	// Proxy all /api/v1/* requests to Python service
	router.Any("/api/v1/*path", proxyRequest)

	// Start server
	port := os.Getenv("GATEWAY_PORT")
	if port == "" {
		port = GATEWAY_PORT
	}

	log.Printf("TouchCLI Gateway listening on :%s", port)
	log.Printf("Agent Service URL: %s", AGENT_SERVICE_URL)
	log.Printf("WebSocket endpoint: ws://localhost:%s/ws", port)

	if err := router.Run(fmt.Sprintf(":%s", port)); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
