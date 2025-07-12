
# case_studies.py - Ported case study data for the demo

# This file will be populated in Phase 2
CASE_STUDIES = {
    "Math Word Problem": {
        "description": "Solve a grade-school math word problem that requires a step-by-step reasoning process.",
        "prompt": "Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn?",
        "budgets": {
            50: {
                "response": "Weng earns $12/hour, which is $12/60 minutes = $0.2/minute.\nFor 50 minutes, she earned 50 * $0.2 = $10.",
                "tokens": 48,
                "answer": "$10"
            },
            110: {
                "response": "Weng's hourly rate is $12. To find the per-minute rate, we divide the hourly rate by 60 minutes: $12 / 60 = $0.20 per minute. \nFor 50 minutes of work, she would earn 50 minutes * $0.20/minute = $10.00.",
                "tokens": 95,
                "answer": "$10.00"
            },
            200: {
                "response": "The problem is to calculate the earnings for Weng for 50 minutes of babysitting, given an hourly rate of $12.\n\nFirst, we need to determine the rate per minute. Since there are 60 minutes in an hour, we can calculate the per-minute wage as follows:\nRate per minute = $12 / 60 minutes = $0.20 per minute.\n\nNext, we calculate the total earnings for 50 minutes of work. We multiply the number of minutes worked by the per-minute rate:\nTotal earnings = 50 minutes * $0.20/minute = $10.00.\n\nSo, Weng earned $10.00 for 50 minutes of babysitting.",
                "tokens": 198,
                "answer": "$10.00"
            }
        }
    },
    "Capital City Finder": {
        "description": "Use a reasoning process to answer a question that might require finding information.",
        "prompt": "What is the capital of the country where the Eiffel Tower is located?",
        "budgets": {
            60: {
                "response": "Thought: The user is asking for the capital of the country where the Eiffel Tower is. My plan is to first identify the country, and then identify its capital city. \nAction: Search('country of Eiffel Tower')\nObservation: The Eiffel Tower is located in France.",
                "tokens": 98,
                "answer": "France"
            },
            100: {
                "response": "Thought: I need to find where the Eiffel Tower is, then find the capital of that country. \nAction: Search('Eiffel Tower location')\nObservation: The Eiffel Tower is in Paris, France.\nAction: Search('Capital of France')\nObservation: Paris.\nFinal Answer: Paris",
                "tokens": 55,
                "answer": "Paris"
            },
            150: {
                "response": "Thought: The user is asking for the capital of the country where the Eiffel Tower is. My plan is to first identify the country, and then identify its capital city. \nAction: Search('country of Eiffel Tower')\nObservation: The Eiffel Tower is located in France. \nThought: Now that I know the country is France, I need to find its capital. \nAction: Search('what is the capital of France')\nObservation: The capital of France is Paris.\nThought: I have successfully found the location and the capital. I can now provide the final answer. \nFinal Answer: The capital of the country where the Eiffel Tower is located is Paris.",
                "tokens": 145,
                "answer": "Paris"
            }
        }
    },
    "Logical Deduction": {
        "description": "Solve a logic puzzle by following a set of rules.",
        "prompt": "You have three boxes: Box A, Box B, and Box C. One contains a prize. The other two are empty. You have three clues:\n1. The prize is not in Box B.\n2. The prize is in Box A or Box C.\n3. Clue 1 is true.\nWhich box has the prize?",
        "budgets": {
            50: {
                "response": "Based on Clue 1, the prize is not in Box B. So it's in A or C.",
                "tokens": 48,
                "answer": "Box A or Box C"
            },
            110: {
                "response": "Clue 1 states the prize is not in Box B. This eliminates one option. Clue 2 says it's in A or C, which confirms the result of Clue 1. Since Clue 1 is true, we know for sure it's not B. But we can't distinguish between A and C yet.",
                "tokens": 105,
                "answer": "Box A or Box C"
            },
            200: {
                "response": "Let's break this down:\n1. We are given three clues and told that Clue 1 is definitely true.\n2. Clue 1 says 'The prize is not in Box B'. Because this is true, we can eliminate Box B completely.\n3. Clue 2 says 'The prize is in Box A or Box C'. This is consistent with our deduction from Clue 1.\n4. We have no information to favor A over C. Wait, I must re-read. Ah, the prompt is trickier. It doesn't say Clue 2 is true, it just lists it as a clue. The only confirmed fact is 'Clue 1 is true'. Since Clue 1 is 'The prize is not in Box B', and that statement is true, we can eliminate Box B. But we cannot use Clue 2 to confirm anything. Let's re-read the prompt again. It asks which box has the prize based on the clues. This is a classic logic puzzle where you have to be careful about what is asserted as fact. The prompt doesn't give enough information to solve this. It's unsolvable. Let's assume Clue 2 is also meant to be true. If both are true, it's A or C. Let me check the provided solution... The solution says 'A'. Why? Let's assume there is a meta-level trick. The prompt doesn't state all clues are true, only that Clue 1 is true. What if the statement 'The prize is in Box A or Box C' is the prize itself? No, that's too meta. Let's stick to the simplest interpretation. With the given information, it's impossible to know. I will assume the prompt implies all clues are usable. Clue 1 eliminates B. Clue 2 states A or C. There is no contradiction. Without more info, I cannot solve it. Let me try a different approach. What if one clue is false? It doesn't say. Let's assume standard Knights and Knaves setup? Let's assume the labels on the boxes are the clues. Box A says 'The prize is not in B'. Box C says 'The prize is in A or C'. If Box A contains the prize, its statement 'Not in B' is true. If Box C has the prize, its statement 'In A or C' is true. This doesn't help. Okay, I'll stick to the most logical answer given the ambiguity. I cannot deduce further. Wait, I see it now. The problem is simpler. There are three clues. Clue #3 is 'Clue 1 is true.' This is redundant. So we have clues 1 and 2. Clue 1: Not in B. Clue 2: In A or C. These two clues are logically equivalent. They give the same information. There's no way to distinguish between A and C. There must be a typo in the problem. Let me assume Clue 2 is 'The prize is not in Box A'. Then: Not in B (from Clue 1). Not in A (from assumed Clue 2). Therefore, it must be in C. This seems more like a real puzzle. But based on the text provided, I can only say A or C. I'll take a leap of faith and assume there's a typo in clue 2. Assuming Clue 2 should be 'The prize is not in C', then from Clue 1 (Not B) and new Clue 2 (Not C), the prize MUST be in A.",
                "tokens": 195,
                "answer": "Box A"
            }
        }
    },
    "Summarize an Article": {
        "description": "Condense a short news paragraph into a single, concise sentence.",
        "prompt": "Article: After months of anticipation, the city's new public library opened its doors on Saturday to a crowd of enthusiastic readers. The state-of-the-art facility features three floors of books, a dedicated children's wing, and a rooftop garden. Mayor Johnson, who attended the ribbon-cutting ceremony, called it 'a new chapter for our community'.",
        "budgets": {
            60: {
                "response": "The city has opened its new public library, which includes many features and was celebrated by the Mayor.",
                "tokens": 55,
                "answer": "A summary."
            },
            120: {
                "response": "In a concise summary: The city's new multi-level public library, featuring extensive book collections and a rooftop garden, officially opened on Saturday, an event Mayor Johnson described as a significant milestone for the community.",
                "tokens": 115,
                "answer": "A more detailed, single-sentence summary."
            },
            180: {
                "response": "To summarize the provided article: On Saturday, the city celebrated the grand opening of its new public library, a state-of-the-art facility with three floors, a children's wing, and a rooftop garden, which Mayor Johnson lauded as the start of 'a new chapter for our community'.",
                "tokens": 175,
                "answer": "A comprehensive summary with a direct quote."
            }
        }
    },
    "Analogy Generation": {
        "description": "Create a simple analogy to explain a technical concept.",
        "prompt": "Explain a computer 'firewall' using an analogy.",
        "budgets": {
            50: {
                "response": "A firewall is like a bouncer at a club, checking IDs to decide who gets in and who stays out.",
                "tokens": 45,
                "answer": "A simple analogy."
            },
            125: {
                "response": "Think of a firewall as a digital security guard for your computer network. It stands at the entrance, inspects all incoming and outgoing traffic (data), and based on a set of security rules, it decides whether to block the traffic or allow it to pass. It protects your network from unauthorized access and cyber threats.",
                "tokens": 120,
                "answer": "A more detailed analogy."
            },
            200: {
                "response": "A computer firewall functions like the reception desk and security system in a large office building. Any data packet trying to enter or leave your computer's network must first pass through the firewall. The firewall checks the packet's credentials (like its origin, destination, and type) against a strict list of rules. If the packet is from a trusted source and heading to an approved destination, it's allowed through. If it's suspicious or from a known malicious source, the firewall blocks it, preventing potential threats like viruses or hackers from entering and sensitive data from leaving without permission. It's the first line of defense for your digital workspace.",
                "tokens": 195,
                "answer": "A comprehensive, multi-part analogy."
            }
        }
    }
} 