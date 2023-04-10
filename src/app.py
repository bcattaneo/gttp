from flask import Flask, request, render_template
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from os import environ
import re
import openai

load_dotenv()

title = "Get To The Point 😠"

app = Flask(__name__)
app.config["DEBUG"] = False
app.config["TEMPLATES_AUTO_RELOAD"] = True
limiter = Limiter(app, key_func=get_remote_address)
CORS(app)

API_KEY = environ.get("API_KEY")
openai.api_key = API_KEY

regex = "Abstract: (.*)[\r\n]+Conclusion: (.*)"
prompt = "Hi ChatGPT. I'll be sending some website articles URLs. The websites are written in HTML, css and probably javascript, but I want you to extract their article's plaintext only, don't show me any code. Write \"Abstract: \" following the processed article's summary. Then leave a blank line and write \"Conclusion: \" following the article's processed short conclusion."
message_log = []


def parse_response(response):
    g = re.search(regex, response)
    if g != None:
        return {
            "abstract": g.group(1),
            "conclusion": g.group(2),
        }
    else:
        return {}


def get_response(message):
    current_message_log = message_log.copy()
    current_message_log.append({"role": "user", "content": message})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=current_message_log,
        max_tokens=1100,
        n=1,
        stop=None,
        temperature=0.7,
    )

    for choice in response.choices:
        if "text" in choice:
            return choice.text

    return response.choices[0].message.content


@app.route("/")
@limiter.limit("1/second")
def home():
    url = request.args.get("url")
    format = request.args.get("format")
    if url != None:
        response = get_response(url)
        parsed_response = parse_response(response)
        if format == "json":
            return parsed_response
        else:
            if len(parsed_response) < 2:
                return render_template("landing.html", title=title)
            else:
                return render_template(
                    "home.html",
                    title=title,
                    url=url,
                    abstract=parsed_response["abstract"],
                    conclusion=parsed_response["conclusion"],
                )
    else:
        return render_template("landing.html", title=title)


def main():
    response = get_response(prompt)
    message_log.append({"role": "user", "content": prompt})
    message_log.append({"role": "assistant", "content": response})
    app.run(host="0.0.0.0", threaded=True, use_reloader=True)


if __name__ == "__main__":
    main()
