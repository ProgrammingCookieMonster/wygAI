from rag import answer_question

test_questions = [
    # swedish questions
    "Hur bokar jag korridor för ett evenemang?",
    "Vem kontaktar jag angående affischer på campus?",
    "Hur organiserar jag ett internt kommittéevenemang?",
    # english questions — should still work
    "How do I book space for an event?",
    # irrelevant — should say it doesn't know
    "Vad är receptet på pannkakor?",
]

for question in test_questions:
    print(f"\n{'='*50}")
    print(f"Q: {question}")
    print(f"A: {answer_question(question)}")