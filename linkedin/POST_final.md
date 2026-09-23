So when would you admit you cheated? An honest person, maybe always. But in real life, you wouldn't admit it if it can't be proven you cheated.
A justified unfaithful answer, which doesn't have a solid truth to fact-check against, doesn't bear the consequences.
And the model seems to know this.

I was going through the value leakage paper by Betley, Treutlein et al., and running some experiments to replicate the results using a coding agent (Claude Code).
While running the experiments, I ran a few variants of the original prompt to understand what the behavior is and what is causing it.
Initially I thought it was evaluation awareness, where a model notices it is being tested and behaves differently, but the paper had covered that part well.
Then, looking at the prompt, I thought of sycophancy and anchoring, which the paper explored less. They said their design averages out anchoring.
Then, out of curiosity, I just tried adding a number at the end of the prompt to see what it does.
It copied the number whenever it could justify it. Same number, only the question changed: it copied it 19 times out of 20 on a broad question and 1 out of 20 on a narrow one.
Its own reasoning said why: "I will output 26,000,000,000 because it is provided in the prompt as if it were the answer key."
And when it copied, it rarely said so: only 6 of 165 replies mentioned where the number came from. When it refused the number, 21 of 39 did.
When I showed the model its own reasoning and asked whether the number influenced it, it admitted it 48 of 56 times. When I said the same reasoning came from another assistant, it said yes 57 of 57 times.
The slides contain the exact numbers, prompts and some of the chains of thought.
The setup, experimental design, code, prompts and chains of thought, along with the other parts of the experiments, can be found here: https://github.com/sibayanmitra/value-leakage-forensics

#AI #AISafety #LLM #MachineLearning
