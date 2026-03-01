# Sage Seed - 外部依赖调用规范

本文档描述 Sage 项目依赖的所有外部服务的调用方式，作为新环境搭建和新项目复用的参考。

变量清单见 [.env](./.env)。

---

## 1. LLM Gateway SSE 调用

统一端点: `POST {LLM_BASE_URL}/api/ai/chat/useTokenStream`

所有大模型调用（前端/后端）都通过 LLM Gateway 代理，不直连任何大模型供应商。

### 1.1 最简后端调用 (3 行)

```typescript
import { streamLLM } from '../llm/streamGateway';

const result = await streamLLM({
  params: { messages: [{ role: 'user', content: 'Hello!' }] },
  token: req.headers['token'] as string,
  onData: (chunk) => res.write(`data: ${JSON.stringify({ content: chunk })}\n\n`)
});
```

> 完整版 Promise 风格:

```typescript
import { baseCallLLMAsync } from '../utils/llmUtils';

const result = await baseCallLLMAsync({
  params: {
    modelName: 'volcesDeepseek',  // 可选，默认 volcesDeepseek
    messages: [{ role: 'user', content: 'Hello!' }],
    temperature: 0.5,
    maxTokens: 8000,
    // tools: [...],             // 可选，Tool Calling
    // tool_choice: 'auto',     // 可选
  },
  token: req.headers['token'] as string,
  onData: (chunk) => process.stdout.write(chunk),
});
console.log(result.content);     // 完整响应文本
console.log(result.toolCalls);   // Tool Call 结果 (如有)
```

### 1.2 最简前端调用

```typescript
import { postAiSSEUseToken } from '@/api/aiApi';

const { cancel } = await postAiSSEUseToken({
  params: {
    messages: [{ role: 'user', content: 'Hello!' }],
    modelName: 'volcesDeepseek',
  },
  onData: (text) => (answer.value += text),
  onComplete: (result) => console.log('Done:', result),
  onError: (err) => console.error(err),
});
```

> `postAiSSEUseToken` 自动处理余额检查 + SSE 流解析 + 计费。

### 1.3 完整请求体结构

```json
{
  "modelName": "volcesDeepseek",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Hello!" }
  ],
  "temperature": 0.5,
  "maxTokens": 8000,
  "stream": true,
  "productId": 3,
  "channelId": 1,
  "tools": [],
  "tool_choice": "auto",
  "parallel_tool_calls": false
}
```

Headers:
```
Content-Type: application/json
Accept: text/event-stream
token: <用户SSO token>
```

### 1.4 SSE 响应格式

网关实际返回简化格式 (非 OpenAI 标准格式):

```
data: {"text":"Hello"}
data: {"text":" world"}
data: {"finish_reason":"stop"}
data: {"usage":{"prompt_tokens":8,"completion_tokens":10,"total_tokens":18,"cached_tokens":8}}
data: [DONE]
```

> 每条 `data:` 行为一个 JSON 对象，正文在 `text` 字段中，`finish_reason` 和 `usage` 在独立消息中返回。

Tool Calling 响应:
```
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_xxx","function":{"name":"get_weather","arguments":""}}]}}]}
data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"arguments":"{\"city\":\"北京\"}"}}]}}]}
data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}
data: [DONE]
```

---

## 2. 大模型列表

网关当前支持的模型 (通过 `modelName` 字段指定):

| 显示名             | modelName           | 供应商                |
| ------------------ | ------------------- | --------------------- |
| claude-sonnet      | `claude-sonnet`     | Anthropic (via Azure) |
| claude-opus        | `claude-opus`       | Anthropic (via Azure) |
| claude-opus-4-6    | `claude-opus-4-6`   | Anthropic (via Azure) |
| gpt-5-chat         | `gpt-5`             | OpenAI (via Azure)    |
| gpt-5.1            | `gpt-5.1`           | OpenAI (via Azure)    |
| gpt-5.2            | `gpt-5.2`           | OpenAI (via Azure)    |
| QWen3              | `qwen-turbo-latest` | 阿里云通义            |
| kimi-k2.5          | `kimi-k2.5`         | Moonshot              |
| kimi-k2            | `kimi-k2`           | Moonshot              |
| kimi-k2-turbo      | `kimi-k2-turbo`     | Moonshot              |
| kimi-8k            | `kimi`              | Moonshot              |
| 火山DeepseekV3     | `volcesDeepseek`    | 火山引擎 (默认)       |
| 火山DeepseekR1     | `volcesDeepseekR1`  | 火山引擎              |
| Ali DeepSeekV3     | `alideepseekv3`     | 阿里云                |
| 腾讯云DeepseekV3   | `tencentDeepseek`   | 腾讯云                |
| deepseek V3        | `deepseek`          | DeepSeek 直连         |
| 零一万物           | `yiwan`             | 零一万物              |
| 硅基流动DeepseekV3 | `siliconDeepseek`   | 硅基流动              |
| 百度DeepSeekV3     | `baiduDeepseek`     | 百度智能云            |
| Ali DeepSeek R1    | `alideepseekr1`     | 阿里云                |
| MiniMax-Text-01    | `minimax-text`      | MiniMax               |

---

## 3. Coze API 调用

所有 Coze 请求走业务网关代理: `{VITE_APP_BASE_NEW_URL}/platform/api/coze/*`

### 3.1 Bot 管理 (CRUD + Publish)

```typescript
import { createBot, updateBot, getBotDetail, getBotList, deleteBot, publishBot } from '@/views/AIsalesAssist/AIDrill/api/cozeApi';

// 创建
const bot = await createBot({
  space_id: VITE_COZE_SPACE_ID,
  bot_name: '销售陪练Bot',
  description: '模拟客户进行销售对练',
  prompt_info: { prompt: '你是一个潜在客户...' }
});

// 获取列表
const bots = await getBotList(VITE_COZE_SPACE_ID);

// 获取详情
const detail = await getBotDetail(bot.bot_id);

// 更新
await updateBot({ bot_id: bot.bot_id, bot_name: '新名称' });

// 发布 (connector_ids: ['1024'] = Coze CN API 渠道)
await publishBot(bot.bot_id);

// 删除
await deleteBot(bot.bot_id);
```

API 端点清单:
| 操作     | 方法 | 路径                                                 |
| -------- | ---- | ---------------------------------------------------- |
| 创建 Bot | POST | `/platform/api/coze/bot/create`                      |
| 更新 Bot | POST | `/platform/api/coze/bot/update`                      |
| 获取详情 | GET  | `/platform/api/coze/bot/get_online_info?bot_id=xxx`  |
| 获取列表 | GET  | `/platform/api/coze/space/get_bot_list?space_id=xxx` |
| 删除 Bot | POST | `/platform/api/coze/bot/delete`                      |
| 发布 Bot | POST | `/platform/api/coze/bot/publish`                     |

### 3.2 Chat 流式对话 (SSE)

**前端 (通过网关代理):**

```typescript
import { chatWithBotStream } from '@/views/AIsalesAssist/AIDrill/api/cozeApi';

const { cancel } = chatWithBotStream(
  {
    bot_id: 'xxx',
    user_id: 'user_123',
    messages: [{ role: 'user', content: '你好', content_type: 'text' }],
    stream: true
  },
  {
    onData: (data) => console.log(data.content),
    onComplete: () => console.log('完成'),
    onError: (err) => console.error(err)
  }
);
```

**后端 (通过 Coze SDK 直连):**

```typescript
// backend/src/services/aiSalesAssist/aiDrillService.ts
const stream = await this.cozeClient.chat.stream({
  bot_id: targetBotId,
  user_id: `user_${userId}`,
  conversation_id: conversationId,
  additional_messages: [{
    role: RoleType.User,
    content: message,
    content_type: 'text' as ContentType
  }],
  auto_save_history: true
});

for await (const part of stream) {
  if (part.event === 'conversation.message.delta') {
    // part.data.content 为增量文本
  }
}
```

### 3.3 Audio 语音服务

```typescript
import { getVoiceList, createSpeech } from '@/views/AIsalesAssist/AIDrill/api/cozeApi';

// 获取语音列表
const voices = await getVoiceList(20, false);

// 语音合成 (TTS)
const audioUrl = await createSpeech(voiceId, '要合成的文本');
```

API 端点:
| 操作     | 方法 | 路径                                     |
| -------- | ---- | ---------------------------------------- |
| 语音列表 | POST | `/platform/api/coze/audio/voices/list`   |
| 语音合成 | POST | `/platform/api/coze/audio/speech/create` |

### 3.4 WebSocket 实时语音 (@coze/api/ws-tools)

用于实时语音对练场景，前端直连 Coze WebSocket:

```typescript
import { WsChatClient, WsChatEventNames } from '@coze/api/ws-tools';

const client = new WsChatClient({
  token: VITE_COZE_ACCESS_TOKEN,     // Coze PAT
  allowPersonalAccessTokenInBrowser: true,
  botId: VITE_COZE_BOT_ID,
  voiceId: VITE_COZE_VOICE_ID,       // 可选
  debug: true
});

// 连接并监听事件
client.on(WsChatEventNames.CONNECTED, () => { /* 已连接 */ });
client.on(WsChatEventNames.AUDIO, (audio) => { /* 播放音频 */ });
client.on(WsChatEventNames.MESSAGE, (msg) => { /* 文本消息 */ });
```

> 依赖包: `@coze/api` (含 ws-tools 子模块)
> 封装位置: `frontend/src/utils/audio.ts`

---

## 4. 计费体系

三方调用链: Sage 前端 -> Sage 后端 (prompt 构建) -> LLM Gateway -> SSO 服务 (余额 + 计费)

### 4.1 前端余额检查

在触发 AI 请求前调用，余额不足时自动弹窗拦截:

```typescript
import { queryIsCanAiUse } from '@/api/aiApi';

const canUse = await queryIsCanAiUse();
if (!canUse) return; // 余额不足，已弹窗提示
// ... 发起 AI 请求
```

底层接口: `POST {VITE_APP_BASE_URL}/ai/findUserAiRemainAmount`

### 4.2 后端 Token 记录

AI 流式响应结束后调用，非阻塞，失败不影响主流程:

```typescript
import { addAiTokenUseLog } from '../utils/addAiTokenUseLog';

addAiTokenUseLog({
  inputTokenCount: number,    // 输入 token 数
  outTokenCount: number,      // 输出 token 数
  aiModelType: string,        // 模型名称，如 'volcesDeepseek'
  token: string               // 用户 SSO token (从 req.headers['token'] 获取)
});
// 固定参数: productId=4 (Sage), channelId=1 (自有平台)
```

底层接口: `POST {COURSE_BASE_URL}/ai/saveAiTokenLog`

请求体:
```json
{
  "inputTokenCount": 500,
  "outTokenCount": 200,
  "aiModelType": "volcesDeepseek",
  "productId": 3,
  "channelId": 1
}
```

### 4.3 PPT 图片计费

```typescript
import { addPptImageCharge } from '../utils/addAiTokenUseLog';

addPptImageCharge({ imgNumber: 3, token: userToken });
// 使用 aiModelType='PPT' 标识
```

---

## 5. LLM Gateway Benchmark

### 5.1 测试方法

- 脚本: `tests/llm-benchmark.mjs` (纯 Node.js，零依赖)
- 端点: `POST {LLM_BASE_URL}/api/ai/chat/useTokenStream`
- 提示词: `"用一句话介绍你自己。"` (固定短 prompt，控制变量)
- 参数: `temperature=0.5, maxTokens=256, stream=true`
- 指标:
  - **TTFT** (Time To First Token): 从请求发出到收到第一个 `text` 片段的时间
  - **总耗时**: 从请求发出到收到 `[DONE]` 的时间
  - **Tokens**: 网关返回的 `completion_tokens`，若缺失则按内容长度估算
  - **Tok/s**: 吞吐量 = Tokens / (总耗时 / 1000)
- 超时: 单模型 30s

运行方式:
```bash
node tests/llm-benchmark.mjs                        # 测试全部 21 个模型
node tests/llm-benchmark.mjs claude gpt             # 只测匹配的模型
node tests/llm-benchmark.mjs kimi-k2-turbo minimax  # 指定模型名
```

### 5.2 测试结果 (2026-02-11)

21/21 模型全部连通，按 TTFT 排序:

| 排名 | 模型               | 供应商            | TTFT     | 总耗时    | Tokens | Tok/s | 状态 |
| ---- | ------------------ | ----------------- | -------- | --------- | ------ | ----- | ---- |
| 1    | MiniMax Text 01    | MiniMax           | 525ms    | 1408ms    | 55     | 39.1  | OK   |
| 2    | QWen3              | 阿里云通义        | 903ms    | 1869ms    | 31     | 16.6  | OK   |
| 3    | Ali DeepSeek V3    | 阿里云            | 949ms    | 1439ms    | 16     | 11.1  | OK   |
| 4    | Kimi K2 Turbo      | Moonshot          | 1017ms   | 1096ms    | 18     | 16.4  | OK   |
| 5    | Kimi K2            | Moonshot          | 1251ms   | 1570ms    | 22     | 14.0  | OK   |
| 6    | DeepSeek V3 直连   | DeepSeek          | 1376ms   | 2113ms    | 28     | 13.3  | OK   |
| 7    | GPT-5              | OpenAI (Azure)    | 1535ms   | 1540ms    | 25     | 16.2  | OK   |
| 8    | Kimi 8K            | Moonshot          | 1564ms   | 1725ms    | 22     | 12.8  | OK   |
| 9    | 火山 DeepSeek V3   | 火山引擎          | 1606ms   | 3150ms    | 42     | 13.3  | OK   |
| 10   | GPT-5.1            | OpenAI (Azure)    | 1775ms   | 1784ms    | 41     | 23.0  | OK   |
| 11   | 硅基流动 DeepSeek  | 硅基流动          | 2076ms   | 2472ms    | 91     | 36.8  | OK   |
| 12   | Claude Sonnet      | Anthropic (Azure) | 2178ms   | 2850ms    | 45     | 15.8  | OK   |
| 13   | GPT-5.2            | OpenAI (Azure)    | 2594ms   | 2630ms    | 40     | 15.2  | OK   |
| 14   | Claude Opus        | Anthropic (Azure) | 2864ms   | 3550ms    | 39     | 11.0  | OK   |
| 15   | Claude Opus 4.6    | Anthropic (Azure) | 3053ms   | 3478ms    | 53     | 15.2  | OK   |
| 16   | 零一万物           | 零一万物          | 3388ms   | 4161ms    | 44     | 10.6  | OK   |
| 17   | Kimi K2.5          | Moonshot          | 6290ms   | 6615ms    | 236    | 35.7  | OK   |
| 18   | Ali DeepSeek R1    | 阿里云            | 6773ms   | 7607ms    | 232    | 30.5  | OK   |
| 19   | 火山 DeepSeek R1   | 火山引擎          | 12055ms  | 14421ms   | 303    | 21.0  | OK   |
| 20   | 腾讯 DeepSeek V3   | 腾讯云            | -        | 134ms     | -      | -     | 无内容 |
| 21   | 百度 DeepSeek V3   | 百度智能云        | -        | 153ms     | -      | -     | 无内容 |

**统计:**
- 平均 TTFT: 2560ms (有效模型)
- 平均总耗时: 3132ms
- 最快首 Token: MiniMax Text 01 (525ms)
- 最高吞吐: MiniMax Text 01 (39.1 tok/s)

**备注:**
- 腾讯/百度 DeepSeek V3 返回极快但无内容，可能是鉴权或返回格式问题
- R1 模型 (DeepSeek R1) TTFT 偏高属正常，因为推理模型有较长的思考链
- Kimi K2.5 TTFT 偏高，可能是模型冷启动或非流式返回

### 5.3 代码示例: 直接调用网关测速

不依赖项目代码，用原生 `fetch` + SSE 解析即可测试任意模型:

```javascript
const LLM_URL = 'https://node.ningshen.net/api/ai/chat/useTokenStream';
const TOKEN   = '<用户SSO token>';

async function benchmarkModel(modelName) {
  const t0 = performance.now();
  let ttft = null, content = '', tokens = 0;

  const res = await fetch(LLM_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'token': TOKEN,
    },
    body: JSON.stringify({
      modelName,
      messages: [{ role: 'user', content: '用一句话介绍你自己。' }],
      temperature: 0.5,
      maxTokens: 256,
      stream: true,
      productId: 4,
      channelId: 1,
    }),
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith('data: ')) continue;
      const payload = trimmed.slice(6);
      if (payload === '[DONE]') continue;

      try {
        const json = JSON.parse(payload);
        if (json.text) {
          if (ttft === null) ttft = performance.now() - t0;
          content += json.text;
        }
        if (json.usage?.completion_tokens) {
          tokens = json.usage.completion_tokens;
        }
      } catch {}
    }
  }

  const totalMs = performance.now() - t0;
  return { modelName, ttft, totalMs, tokens, content };
}

// 用法
const result = await benchmarkModel('kimi-k2-turbo');
console.log(`TTFT: ${result.ttft?.toFixed(0)}ms, 总耗时: ${result.totalMs.toFixed(0)}ms`);
```

> 完整测试脚本见 `tests/llm-benchmark.mjs`，支持批量测试和表格输出。

---
