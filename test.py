from rag import answer_question

test_questions = [
    # booking kårhuset
    "Hur bokar jag en lokal i kårhuset?",
    "Vilken mailadress använder jag för att boka kårhusets lokaler?",
    # alcohol policy
    "What exactly is the CANON-education?",
    "Vilka krav finns för att bli serveringsansvarig?",
    # committees
    "Vad är skillnaden mellan ett programutskott och ett intresseutskott?",
    "Vad händer om ett utskott inte följer arbetsordningen?",
    # student representative
    "Vem kontaktar jag om jag vill avsluta mitt uppdrag som studentrepresentant?",
    # english
    "How do I book the student union house for an event?",
    # irrelevant — should be blocked
    "Vad är receptet på pannkakor?",
    "How do i book a table on a restaurant?",
]

for question in test_questions:
    print(f"\n{'='*50}")
    print(f"Q: {question}")
    print(f"A: {answer_question(question, debug=False)}")