/**
 * OpenClaw Plugin SDK 类型定义
 *
 * 当前为 v0.1 开发阶段的内联类型，待 @openclaw/plugin-sdk 正式发布后替换为包引用。
 * 参考: https://github.com/openclaw/openclaw
 */

// ============================================================
// Plugin 注册
// ============================================================

export interface PluginManifest {
  name: string;
  version: string;
  displayName: string;
  description: string;
  entry: string;
  engines: { openclaw: string };
  contributes?: {
    tools?: ToolContribution[];
  };
  config?: {
    properties: Record<string, ConfigProperty>;
  };
}

export interface ToolContribution {
  name: string;
  description: string;
}

export interface ConfigProperty {
  type: string;
  default: unknown;
  description: string;
}

// ============================================================
// Tool 定义
// ============================================================

/** JSON Schema 定义（OpenClaw 内部用） */
export interface JSONSchema {
  type?: string;
  description?: string;
  properties?: Record<string, JSONSchema>;
  required?: string[];
  items?: JSONSchema;
  enum?: string[];
  default?: unknown;
}

/** Tool 处理器签名 */
export type ToolHandler = (
  input: Record<string, unknown>,
  context: ToolContext,
) => Promise<unknown>;

/** Tool 定义 */
export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: JSONSchema;
  handler: ToolHandler;
}

/** Tool 执行上下文 */
export interface ToolContext {
  /** 会话 ID（跨轮对话关联用） */
  sessionId: string;
  /** 中止信号 */
  signal: AbortSignal;
  /** 插件配置 */
  config: Record<string, unknown>;
}

// ============================================================
// Approval（审批流）
// ============================================================

export interface ApprovalRequest {
  /** 审批标题 */
  title: string;
  /** 审批内容（Markdown） */
  body: string;
  /** 操作风险等级 */
  severity: 'info' | 'warning' | 'critical';
  /** 审批超时（毫秒） */
  timeoutMs?: number;
  /** 操作标签（用于回调识别） */
  actionId: string;
}

export type ApprovalVerdict = 'approved' | 'rejected' | 'timeout';

export interface ApprovalResult {
  verdict: ApprovalVerdict;
  reason?: string;
  actionId: string;
}

export interface ApprovalRuntime {
  request(req: ApprovalRequest): Promise<ApprovalResult>;
}

// ============================================================
// Push Channel（主动推送）
// ============================================================

export interface ChannelMessage {
  title: string;
  body: string;
  severity: 'info' | 'warning' | 'error';
  /** 点击消息时执行的动作 */
  action?: {
    type: string;
    payload: Record<string, unknown>;
  };
}

export interface ChannelRuntime {
  send(message: ChannelMessage): Promise<void>;
}

// ============================================================
// Plugin Context
// ============================================================

export interface PluginContext {
  /** 注册一个工具 */
  registerTool(tool: ToolDefinition): void;
  /** 访问插件配置 */
  config: Record<string, unknown>;
  /** 审批运行时 */
  approval?: ApprovalRuntime;
  /** 消息通道（主动推送） */
  channel?: ChannelRuntime;
  /** 日志 */
  log: {
    info(msg: string, ...args: unknown[]): void;
    warn(msg: string, ...args: unknown[]): void;
    error(msg: string, ...args: unknown[]): void;
  };
}

/** Plugin 注册函数签名 */
export type PluginRegister = (context: PluginContext) => void | Promise<void>;

export interface PluginDefinition {
  name: string;
  version: string;
  description: string;
  register: PluginRegister;
}

/** 插件入口定义函数 */
export function definePlugin(def: PluginDefinition): PluginDefinition {
  return def;
}
