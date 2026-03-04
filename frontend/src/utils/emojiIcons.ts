/**
 * Emoji → Iconify icon mapping utility
 * Replaces known emoji characters with Iconify icon names for consistent rendering
 */

export interface TextSegment {
    type: 'text'
    value: string
}

export interface IconSegment {
    type: 'icon'
    emoji: string
    iconName: string // 将 path 和 fill 替换为 Iconify 的图标名称
}

export type Segment = TextSegment | IconSegment

// 将 Emoji 映射到具体的 Iconify 图标 (格式为 "图标集:图标名")
const EMOJI_ICONS: Record<string, string> = {
    '🤖': 'mdi:robot-outline',          // Material Design Icons
    '📍': 'lucide:map-pin',             // Lucide Icons
    '💬': 'lucide:message-circle',
    '⚡': 'catppuccin:zap',
    '🔍': 'lucide:search',
    '✅': 'lucide:check-circle',
    '🧠': 'twemoji:brain',
    '👤': 'glyphs-poly:user',
    '🚦': 'streamline-plump:traffic-light-solid',
    '📋': 'lucide:clipboard-list',
}

// 动态生成正则表达式以匹配映射表中的 Emoji
const emojiPattern = new RegExp(
    `(${Object.keys(EMOJI_ICONS).map(e => e.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`,
    'g'
)

export function parseEmojiText(text: string): Segment[] {
    const segments: Segment[] = []
    let lastIndex = 0
    emojiPattern.lastIndex = 0

    let match: RegExpExecArray | null
    while ((match = emojiPattern.exec(text)) !== null) {
        // 提取 Emoji 之前的纯文本
        if (match.index > lastIndex) {
            segments.push({ type: 'text', value: text.slice(lastIndex, match.index) })
        }

        const emoji = match[0]
        const iconName = EMOJI_ICONS[emoji]

        // 如果在映射表中找到了对应的图标名，则存入 iconName
        if (iconName) {
            segments.push({ type: 'icon', emoji, iconName })
        }

        lastIndex = match.index + match[0].length
    }

    // 提取最后剩余的文本
    if (lastIndex < text.length) {
        segments.push({ type: 'text', value: text.slice(lastIndex) })
    }

    return segments
}

export function stripEmoji(text: string): string {
    emojiPattern.lastIndex = 0
    return text.replace(emojiPattern, '').trim()
}