import os
from openai import OpenAI

# Read from environment variable
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get API key from env or ask the user
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    api_key = input("Enter your OpenAI API key (it will not be saved): ").strip()

client = OpenAI(api_key=api_key)

def analyze_logs():
    with open("samples/webserver_logs.txt", "r") as f:
        logs = f.read()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an SRE copilot that explains incidents clearly."},
            {"role": "user", "content": logs}
        ]
    )

    print("\n=== DevOps Copilot Output ===\n")
    #print(response.choices[0].message["content"])
    print(response.choices[0].message.content)

if __name__ == "__main__":
    analyze_logs()
