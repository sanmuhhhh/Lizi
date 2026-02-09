import { tool } from "@opencode-ai/plugin"

// ─── 类型定义 ────────────────────────────────────────────────────────────────

type ReliabilityKind = "BEST_EFFORT" | "RELIABLE"
type DurabilityKind = "VOLATILE" | "TRANSIENT_LOCAL" | "TRANSIENT" | "PERSISTENT"
type LivelinessKind = "AUTOMATIC" | "MANUAL_BY_PARTICIPANT" | "MANUAL_BY_TOPIC"
type OwnershipKind = "SHARED" | "EXCLUSIVE"

interface WriterQoS {
  reliability?: ReliabilityKind
  durability?: DurabilityKind
  deadline_ms?: number
  liveliness_kind?: LivelinessKind
  liveliness_lease_ms?: number
  ownership?: OwnershipKind
}

interface ReaderQoS {
  reliability?: ReliabilityKind
  durability?: DurabilityKind
  deadline_ms?: number
  liveliness_kind?: LivelinessKind
  liveliness_lease_ms?: number
  ownership?: OwnershipKind
}

interface CheckResult {
  compatible: boolean
  issues: Issue[]
  summary: string
  spec_ref: string
}

interface Issue {
  policy: string
  result: "INCOMPATIBLE" | "OK"
  writer: string
  reader: string
  rule: string
  spec: string
}

// ─── 枚举归一化 ──────────────────────────────────────────────────────────────
// AI 从代码中读取的宏名、小写形式、中文描述，统一转换为标准枚举值

function normalizeReliability(v: string | undefined): ReliabilityKind {
  if (!v) return "BEST_EFFORT"
  const s = v.toUpperCase().replace(/DDS_RELIABILITY_/g, "").replace(/-/g, "_")
  if (s.includes("RELIABLE") && !s.includes("BEST")) return "RELIABLE"
  return "BEST_EFFORT"
}

function normalizeDurability(v: string | undefined): DurabilityKind {
  if (!v) return "VOLATILE"
  const s = v.toUpperCase().replace(/DDS_DURABILITY_/g, "").replace(/-/g, "_")
  if (s.includes("PERSISTENT")) return "PERSISTENT"
  if (s.includes("TRANSIENT_LOCAL") || s.includes("LOCAL")) return "TRANSIENT_LOCAL"
  if (s.includes("TRANSIENT")) return "TRANSIENT"
  return "VOLATILE"
}

function normalizeLivelinessKind(v: string | undefined): LivelinessKind {
  if (!v) return "AUTOMATIC"
  const s = v.toUpperCase().replace(/DDS_LIVELINESS_/g, "").replace(/-/g, "_")
  if (s.includes("TOPIC")) return "MANUAL_BY_TOPIC"
  if (s.includes("PARTICIPANT")) return "MANUAL_BY_PARTICIPANT"
  return "AUTOMATIC"
}

function normalizeOwnership(v: string | undefined): OwnershipKind {
  if (!v) return "SHARED"
  const s = v.toUpperCase().replace(/DDS_OWNERSHIP_/g, "")
  if (s.includes("EXCLUSIVE")) return "EXCLUSIVE"
  return "SHARED"
}

// ─── 兼容性检查逻辑 ──────────────────────────────────────────────────────────

const RELIABILITY_ORDER: Record<ReliabilityKind, number> = { BEST_EFFORT: 0, RELIABLE: 1 }
const DURABILITY_ORDER: Record<DurabilityKind, number> = { VOLATILE: 0, TRANSIENT_LOCAL: 1, TRANSIENT: 2, PERSISTENT: 3 }
const LIVELINESS_ORDER: Record<LivelinessKind, number> = { AUTOMATIC: 0, MANUAL_BY_PARTICIPANT: 1, MANUAL_BY_TOPIC: 2 }

function checkReliability(writer: WriterQoS, reader: ReaderQoS): Issue {
  const w = normalizeReliability(writer.reliability)
  const r = normalizeReliability(reader.reliability)
  return {
    policy: "RELIABILITY",
    result: RELIABILITY_ORDER[w] >= RELIABILITY_ORDER[r] ? "OK" : "INCOMPATIBLE",
    writer: w, reader: r,
    rule: "offered >= requested（BEST_EFFORT < RELIABLE）",
    spec: "DDS v1.4 §2.2.3.6",
  }
}

function checkDurability(writer: WriterQoS, reader: ReaderQoS): Issue {
  const w = normalizeDurability(writer.durability)
  const r = normalizeDurability(reader.durability)
  return {
    policy: "DURABILITY",
    result: DURABILITY_ORDER[w] >= DURABILITY_ORDER[r] ? "OK" : "INCOMPATIBLE",
    writer: w, reader: r,
    rule: "offered >= requested（VOLATILE < TRANSIENT_LOCAL < TRANSIENT < PERSISTENT）",
    spec: "DDS v1.4 §2.2.3.4",
  }
}

function checkDeadline(writer: WriterQoS, reader: ReaderQoS): Issue {
  const w = writer.deadline_ms ?? -1
  const r = reader.deadline_ms ?? -1
  // writer infinite + reader 有限 → 不兼容（writer 无法保证在 reader 期望周期内更新）
  const compatible = w === -1 ? r === -1 : (r === -1 || w <= r)
  return {
    policy: "DEADLINE",
    result: compatible ? "OK" : "INCOMPATIBLE",
    writer: w === -1 ? "infinite" : `${w}ms`,
    reader: r === -1 ? "infinite" : `${r}ms`,
    rule: "offered.period <= requested.period",
    spec: "DDS v1.4 §2.2.3.7",
  }
}

function checkLiveliness(writer: WriterQoS, reader: ReaderQoS): Issue {
  const wKind = normalizeLivelinessKind(writer.liveliness_kind)
  const rKind = normalizeLivelinessKind(reader.liveliness_kind)
  const wLease = writer.liveliness_lease_ms ?? -1
  const rLease = reader.liveliness_lease_ms ?? -1
  const kindOk = LIVELINESS_ORDER[wKind] >= LIVELINESS_ORDER[rKind]
  const leaseOk = wLease === -1 ? rLease === -1 : (rLease === -1 || wLease <= rLease)
  return {
    policy: "LIVELINESS",
    result: kindOk && leaseOk ? "OK" : "INCOMPATIBLE",
    writer: `${wKind}, lease=${wLease === -1 ? "infinite" : wLease + "ms"}`,
    reader: `${rKind}, lease=${rLease === -1 ? "infinite" : rLease + "ms"}`,
    rule: "offered kind >= requested kind，且 offered.lease <= requested.lease",
    spec: "DDS v1.4 §2.2.3.11",
  }
}

function checkOwnership(writer: WriterQoS, reader: ReaderQoS): Issue {
  const w = normalizeOwnership(writer.ownership)
  const r = normalizeOwnership(reader.ownership)
  return {
    policy: "OWNERSHIP",
    result: w === r ? "OK" : "INCOMPATIBLE",
    writer: w, reader: r,
    rule: "offered kind 必须与 requested kind 完全相同",
    spec: "DDS v1.4 §2.2.3.9",
  }
}

// ─── 工具入口 ────────────────────────────────────────────────────────────────

const DESCRIPTION = [
  "检查 DDS DataWriter 与 DataReader 的 QoS 兼容性。",
  "",
  "涵盖 5 条 RxO 策略：RELIABILITY / DURABILITY / DEADLINE / LIVELINESS / OWNERSHIP",
  "",
  "【枚举值识别】调用前无需手动转换，以下形式均可识别：",
  "  RELIABILITY:  BEST_EFFORT / RELIABLE / DDS_RELIABILITY_* / 可靠 / 尽力",
  "  DURABILITY:   VOLATILE / TRANSIENT_LOCAL / TRANSIENT / PERSISTENT / DDS_DURABILITY_*",
  "  LIVELINESS:   AUTOMATIC / MANUAL_BY_PARTICIPANT / MANUAL_BY_TOPIC / DDS_LIVELINESS_*",
  "  OWNERSHIP:    SHARED / EXCLUSIVE / DDS_OWNERSHIP_*",
  "",
  "【时间参数】deadline_ms / liveliness_lease_ms 单位为毫秒，-1 或不传表示 infinite",
  "",
  "用法示例:",
  '  dds_qos_check({ writer: { reliability: "BEST_EFFORT" }, reader: { reliability: "RELIABLE" } })',
  '  dds_qos_check({ writer: { deadline_ms: 1000 }, reader: { deadline_ms: 500 } })',
].join("\n")

export default tool({
  description: DESCRIPTION,

  args: {
    writer: tool.schema.object({
      reliability: tool.schema.string().optional().describe("BEST_EFFORT / RELIABLE / DDS_RELIABILITY_* / 可靠 / 尽力，默认 BEST_EFFORT"),
      durability: tool.schema.string().optional().describe("VOLATILE / TRANSIENT_LOCAL / TRANSIENT / PERSISTENT / DDS_DURABILITY_*，默认 VOLATILE"),
      deadline_ms: tool.schema.number().optional().describe("单位 ms，-1 表示 infinite，默认 infinite"),
      liveliness_kind: tool.schema.string().optional().describe("AUTOMATIC / MANUAL_BY_PARTICIPANT / MANUAL_BY_TOPIC / DDS_LIVELINESS_*，默认 AUTOMATIC"),
      liveliness_lease_ms: tool.schema.number().optional().describe("单位 ms，-1 表示 infinite，默认 infinite"),
      ownership: tool.schema.string().optional().describe("SHARED / EXCLUSIVE / DDS_OWNERSHIP_*，默认 SHARED"),
    }).describe("DataWriter 的 QoS 配置"),

    reader: tool.schema.object({
      reliability: tool.schema.string().optional().describe("BEST_EFFORT / RELIABLE / DDS_RELIABILITY_* / 可靠 / 尽力，默认 BEST_EFFORT"),
      durability: tool.schema.string().optional().describe("VOLATILE / TRANSIENT_LOCAL / TRANSIENT / PERSISTENT / DDS_DURABILITY_*，默认 VOLATILE"),
      deadline_ms: tool.schema.number().optional().describe("单位 ms，-1 表示 infinite，默认 infinite"),
      liveliness_kind: tool.schema.string().optional().describe("AUTOMATIC / MANUAL_BY_PARTICIPANT / MANUAL_BY_TOPIC / DDS_LIVELINESS_*，默认 AUTOMATIC"),
      liveliness_lease_ms: tool.schema.number().optional().describe("单位 ms，-1 表示 infinite，默认 infinite"),
      ownership: tool.schema.string().optional().describe("SHARED / EXCLUSIVE / DDS_OWNERSHIP_*，默认 SHARED"),
    }).describe("DataReader 的 QoS 配置"),
  },

  async execute(args) {
    const { writer, reader } = args

    const issues: Issue[] = [
      checkReliability(writer, reader),
      checkDurability(writer, reader),
      checkDeadline(writer, reader),
      checkLiveliness(writer, reader),
      checkOwnership(writer, reader),
    ]

    const incompatible = issues.filter(i => i.result === "INCOMPATIBLE")
    const compatible = incompatible.length === 0

    const result: CheckResult = {
      compatible,
      issues,
      summary: compatible
        ? "兼容 ✅ 所有 QoS 策略均满足"
        : `不兼容 ❌ ${incompatible.map(i => i.policy).join(", ")}`,
      spec_ref: "DDS v1.4 §2.2.3",
    }

    return JSON.stringify(result, null, 2)
  },
})
