# Text to Morse Code Converter

morse_code = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
    'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
    'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-',
    'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
    'Y': '-.--', 'Z': '--..',
    '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....',
    '6': '-....', '7': '--...', '8': '---..',
    '9': '----.',
    ' ': '/'
}

print("================================")
print("     MORSE CODE CONVERTER")
print("================================")

text = input("Enter a message to convert: ").upper()

morse_result = []

for char in text:
    if char in morse_code:
        morse_result.append(morse_code[char])
    else:
        morse_result.append('?')

print("\nOriginal Message:", text)
print("Morse Code:", ' '.join(morse_result))
print("\nConversion completed!")