import type { Persona } from '../types'

const AVATAR_BY_PERSONA_ID: Record<string, string> = {
  hard_boss: '/avatars/hard_boss.png',
  tech_savvy: '/avatars/tech_savvy.png',
  young_mother: '/avatars/young_mother.png',
  eager_youth: '/avatars/eager_youth.png',
  hidden_risk_client: '/avatars/hidden_risk_client.png',
  rebate_seeker: '/avatars/rebate_seeker.png',
}

export function personaAvatar(persona?: Pick<Persona, 'persona_id'> | null): string | undefined {
  return persona ? AVATAR_BY_PERSONA_ID[persona.persona_id] : undefined
}
