
# WP3.6: Role-specific formality and anti-repetition
FORMALITY_LEVELS = {'family': 0.3, 'friend': 0.4, 'mentor': 0.5, 'colleague': 0.6, 'partner': 0.4}
ANTI_REPETITION = 'Avoid repeating phrases used in previous 3 turns. Use varied sentence structures. Do not reuse the same opening or closing pattern within the same conversation.'

def _injectStyleDirective(role_type, base_prompt):
    formality = FORMALITY_LEVELS.get(role_type, 0.5)
    style = f'Formality level: {formality}. '
    if formality < 0.5:
        style += 'Use casual, warm language. Occasional colloquialisms are appropriate. '
    else:
        style += 'Maintain professional but approachable tone. '
    return base_prompt + '\n' + style + ANTI_REPETITION

def getConversationPrompt// 2026-06-01T14:00:00 — feat(conv): implement emotion-aware tone adaptation module (WP3.6 phase 2)
