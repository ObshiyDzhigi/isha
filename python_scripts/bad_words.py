from better_profanity import profanity

text = input('Type a bad word and i will censor it: ')

open_file = profanity.load_censor_words_from_file('censor.txt')

print(profanity.censor(text))
print(profanity.contains_profanity(text))