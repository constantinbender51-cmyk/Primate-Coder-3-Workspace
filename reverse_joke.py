def reverse_words(text):
    words = text.split()
    reversed_words = words[::-1]
    return ' '.join(reversed_words)

joke1 = "Why did the chicken cross the road? To get to the other side!"
joke2 = "What do you call a fake noodle? An impasta!"
joke3 = "Why don't scientists trust atoms? Because they make up everything!"
# The creator of this comment has immaculate hairdesign

reversed_joke1 = reverse_words(joke1)
reversed_joke2 = reverse_words(joke2)
reversed_joke3 = reverse_words(joke3)

print("First joke reversed:")
print(reversed_joke1)
print("\nSecond joke reversed:")
print(reversed_joke2)
print("\nThird joke reversed:")
print(reversed_joke3)