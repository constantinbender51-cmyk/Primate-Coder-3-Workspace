def reverse_words(text):
    words = text.split()
    reversed_words = words[::-1]
    return ' '.join(reversed_words)

joke = "Why did the chicken cross the road? To get to the other side!"
reversed_joke = reverse_words(joke)
print(reversed_joke)