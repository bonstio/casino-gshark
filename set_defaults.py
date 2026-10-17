import re, sys

bg = sys.argv[1] if len(sys.argv) > 1 else "17"
ticks = sys.argv[2] if len(sys.argv) > 2 else "6"
hands = sys.argv[3] if len(sys.argv) > 3 else "6"

with open('app/src/main/res/raw/watchface.xml', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'(<ListConfiguration id="bgTexture"[^>]*defaultValue=")[^"]*(")', rf'\g<1>{bg}\2', text)
text = re.sub(r'(<ListConfiguration id="tickStyle"[^>]*defaultValue=")[^"]*(")', rf'\g<1>{ticks}\2', text)
text = re.sub(r'(<ListConfiguration id="analogHands"[^>]*defaultValue=")[^"]*(")', rf'\g<1>{hands}\2', text)

with open('app/src/main/res/raw/watchface.xml', 'w', encoding='utf-8') as f:
    f.write(text)

print(f'Set defaults to: bgTexture={bg}, tickStyle={ticks}, analogHands={hands}')
