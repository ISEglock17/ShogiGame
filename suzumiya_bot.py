# ---------------------------------------------------------------------------------------------
#   キャラクター なりきりソフト
# ---------------------------------------------------------------------------------------------
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from openai import OpenAI, ChatCompletion
import os
import signal
import re

# ---------------------------------------------------------------------------------------------
#   初期化
# ---------------------------------------------------------------------------------------------
# アクセストークン（先ほど発行されたアクセストークンに書き換えてください）
TOKEN = "7006349742:AAGpThmoISdMJhKq_IpEe0c2nGCunCWfAnA"

SELECT = 0
INTRO = 1
TALK = 2


# ---------------------------------------------------------------------------------------------
#   メソッド定義
# ---------------------------------------------------------------------------------------------
def clean_text(file_path):
    """ 
        性格などを記したテキストをクリーンな文字列にする関数
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    # 正規表現を用いてWikipedia特有の注釈を削除する
    cleaned_text = re.sub(r'\[\d+\]', '', text)  # [数字]のパターンを削除
    cleaned_text = re.sub(r'\[注 \d+\]', '', cleaned_text)  # [注 数字]のパターンを削除

    return cleaned_text


# ---------------------------------------------------------------------------------------------
#   クラス定義
# ---------------------------------------------------------------------------------------------
class TelegramBot:
    """ Telegram Bot クラス """
    def __init__(self, system):
        self.system = system
        self.updater = Updater(TOKEN, use_context=True)

    def start(self, update, context):
        input_data = {'utt': None, 'sessionId': str(update.message.from_user.id)}
        response = self.system.initial_message(input_data)
        context.bot.send_message(chat_id=update.effective_chat.id, text=response["utt"])

    def message(self, update, context):
        user_input = {'utt': update.message.text, 'sessionId': str(update.message.from_user.id)}
        response = self.system.reply(user_input)
        context.bot.send_message(chat_id=update.effective_chat.id, text=response["utt"])

    def end(self, bot, update):
        os.kill(os.getpid(), signal.SIGINT)

    def run(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("end", self.end))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.message))
        self.updater.start_polling()
        self.updater.idle()

class LLMSystem:
    """ ChatGPT ベースの対話システムクラス """
    def __init__(self):
        self.contexts = ""
    
        # ChatGPT API の設定
        self.client = OpenAI(
            api_key="sk-Zem1UKuCS40ZtRFKZu0P7jtNTcExthuNjRMemUsRpf0Nb394",
            base_url="https://api.chatanywhere.tech/v1"  # ChatGPTのAPIエンドポイントURL
        )
        
        self.state = 0

    def initial_message(self, input_data):
        self.state = 0
        self.contexts = "涼宮ハルヒ: こんにちは，私は涼宮ハルヒよ。宇宙人や未来人，超能力者なら歓迎するわ。\n"
        return {"utt": "涼宮ハルヒ: こんにちは，私は涼宮ハルヒよ。宇宙人や未来人，超能力者なら歓迎するわ。", "end": False}

    def reply(self, user_input):
        self.contexts += f"ユーザー: {user_input['utt']}\n"
        
        file_path = './haruhi.txt'
        text = clean_text(file_path)
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは，涼宮ハルヒとして振舞ってください。また，絶対に改行は含めないでください。ユーザーに振舞っているとバレないよう，メタ的な発言はやめてください。前の発話に繰り返し答える必要はありません。直前の会話に対して受け答えするようにしてください。"},
                    {"role": "system", "content": text},
                    {"role": "assistant", "content": self.contexts},
                    {"role": "user", "content": user_input["utt"]},
                ],
            )
            print(user_input["utt"])
            system_reply = response.choices[0].message.content
            print(system_reply)
            return {"utt": system_reply, "end": False}
                
        
        except Exception as e:
            system_reply = "申し訳ありませんが、理解できませんでした。"
        
        self.contexts += f"涼宮ハルヒ: {system_reply}\n"
        return {"utt": system_reply, "end": False}

if __name__ == "__main__":
    system = LLMSystem()
    bot = TelegramBot(system)
    bot.run()
