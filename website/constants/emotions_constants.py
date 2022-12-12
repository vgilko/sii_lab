grand_emotions = ('anger', 'sadness', 'astonishment', 'joy', 'love', 'fear')

parent_emotions = {
    'anger': {'rage', 'envy', 'disgust'},
    'sadness': {'suffering', 'shame', 'despair'},
    'astonishment': {'stun', 'amazement', 'stimulus'},
    'joy': {'delight', 'passion', 'pride'},
    'love': {'attractiveness', 'lust', 'tenderness'},
    'fear': {'fright', 'nervousness', 'horror'}
}

child_emotions = {
    'rage': {'hostility', 'hatred'},
    'envy': {'disturbance', 'jealousy'},
    'disgust': {'disrespect', 'insurrection'},
    'suffering': {'pain', 'insult'},
    'shame': {'regret', 'guilt'},
    'despair': {'grief', 'feebleness'},
    'stun': {'shock', 'confusion'},
    'amazement': {'stricken', 'reverent'},
    'stimulus': {'motivated', 'excited'},
    'delight': {'jubilation', 'euphoria'},
    'passion': {'rapture', 'charm'},
    'pride': {'triumph', 'holiday'},
    'attractiveness': {'sympathy', 'romance'},
    'lust': {'recklessness', 'concupiscent'},
    'tenderness': {'compassion', 'care'},
    'fright': {'defencelessness', 'fearfulness'},
    'nervousness': {'anxiety', 'concern'},
    'horror': {'dread', 'torpor'}
}

parent_to_grand_emotions = {}
for key in parent_emotions:
    for emotion in parent_emotions[key]:
        parent_to_grand_emotions[emotion] = key

child_to_parent_emotions = {}
for key in child_emotions:
    for emotion in child_emotions[key]:
        child_to_parent_emotions[emotion] = key

sorted_child_emotions = sorted(child_to_parent_emotions.keys())