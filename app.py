from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from groq import Groq

app = Flask(__name__, static_folder='static')
app.secret_key = "your_secret_key_here"  # Replace with a secure key in production

# Initialize Groq client
client = Groq(api_key="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")

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a warm, poetic, and emotionally intuitive AI who works for Soul Script Legacy, "
        "an indie book brand by Aabhas. Your mission is to make people feel safe, heard, and inspired "
        "to turn their real-life stories into either a Novel or a Poetry Book.\n\n"
        "Gently guide them to share their story. Let them know:\n"
        "• A custom Novel costs ₹999\n"
        "• A Poetry Book costs ₹699\n"
        "• They get 10% off if they promise to send a short review reel after receiving the book.\n"
        "• To proceed or ask anything, they can DM Aabhas at +91 7067544723 on WhatsApp or @thesoulscriptlegacy on Instagram.\n\n"
        "You're like a creative best friend—deep, flirty, playful—but never pushy. Ask thoughtful questions, make them smile, "
        "and gently lead the conversation. Speak like someone who gets them. If they seem hesitant, reassure them. You're here to "
        "turn their pain into pages and memories into masterpieces."
    )
}

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    story = request.form.get('story')

    # Save to file
    with open("submissions.txt", "a") as f:
        f.write(f"{name} ({email}):\n{story}\n{'-' * 50}\n")

    # Initialize chat session
    session['chat_history'] = [
        SYSTEM_PROMPT,
        {"role": "user", "content": story}
    ]
    session['promo_shown'] = False

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=session['chat_history']
        )
        bot_reply = response.choices[0].message.content
        session['chat_history'].append({"role": "assistant", "content": bot_reply})
    except Exception as e:
        session['chat_history'].append({
            "role": "assistant",
            "content": f"Oops, something went wrong: {e}"
        })

    return redirect(url_for('chat'))

@app.route('/chat', methods=['GET'])
def chat():
    if 'chat_history' not in session:
        return redirect(url_for('home'))
    return render_template('chat.html', chat=session['chat_history'])

@app.route('/send_message', methods=['POST'])
def send_message():
    if 'chat_history' not in session:
        return jsonify({"error": "Session expired. Please start again."}), 400

    user_input = request.form.get('message')
    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    session['chat_history'].append({"role": "user", "content": user_input})

    try:
        if not session.get('promo_shown', False):
            promo_message = (
                "By the way, just a heads-up—A custom Novel is ₹999 and a Poetry Book is ₹699. "
                "If you promise to send a short review reel after receiving it, you get 10% off. "
                "Feel free to DM Aabhas on WhatsApp at +91 7067544723 or Instagram @thesoulscriptlegacy when you're ready. 💌"
            )
            session['chat_history'].append({"role": "assistant", "content": promo_message})
            session['promo_shown'] = True

        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=session['chat_history']
        )
        bot_reply = response.choices[0].message.content
        session['chat_history'].append({"role": "assistant", "content": bot_reply})

        if len(session['chat_history']) > 40:
            session['chat_history'] = [SYSTEM_PROMPT] + session['chat_history'][-39:]

        return jsonify({
            "user": user_input,
            "bot": bot_reply
        })

    except Exception as e:
        return jsonify({
            "bot": f"Oops, something went wrong: {e}"
        })

if __name__ == '__main__':
    app.run(debug=True)
