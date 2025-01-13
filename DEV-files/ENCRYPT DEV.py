def vigenere_encrypt(key, text):
    encrypted_text = []
    key = key.upper()
    key_length = len(key)

    for i, char in enumerate(text):
        if char.isalpha():  # Проверяем, является ли символ буквой
            is_upper = char.isupper()
            shift = ord(key[i % key_length]) - ord('A')
            base = ord('A') if is_upper else ord('a')

            # Шифрование символа с учетом сдвига
            encrypted_char = chr((ord(char) - base + shift) % 26 + base)
            encrypted_text.append(encrypted_char)
        else:
            # Оставляем символ без изменений, если это не буква
            encrypted_text.append(char)

    return ''.join(encrypted_text)


# Чтение входных данных
key = input("Введите ключ: ")
text = input("Введите текст для шифрования: ")

# Шифрование текста
encrypted_text = vigenere_encrypt(key, text)
print("Зашифрованный текст:", encrypted_text)
