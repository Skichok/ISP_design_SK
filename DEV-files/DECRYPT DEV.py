def vigenere_decrypt(key, text):
    decrypted_text = []
    key = key.upper()
    key_length = len(key)

    for i, char in enumerate(text):
        if char.isalpha():  # Проверяем, является ли символ буквой
            is_upper = char.isupper()
            shift = ord(key[i % key_length]) - ord('A')
            base = ord('A') if is_upper else ord('a')

            # Дешифрование символа с учетом сдвига
            decrypted_char = chr((ord(char) - base - shift) % 26 + base)
            decrypted_text.append(decrypted_char)
        else:
            # Оставляем символ без изменений, если это не буква
            decrypted_text.append(char)

    return ''.join(decrypted_text)


# Чтение входных данных
key = input("Введите ключ: ")
text = input("Введите зашифрованный текст: ")

# Дешифрование текста
decrypted_text = vigenere_decrypt(key, text)
print("Расшифрованный текст:", decrypted_text)
