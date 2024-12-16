import subprocess
import time

#-----------------------------------------------------------------------------------
#　やねうら王の動作
#-----------------------------------------------------------------------------------
def start_yaneuraou(executable_path):
    """やねうら王のプロセスを起動"""
    process = subprocess.Popen(
        [executable_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='shift_jis'
    )
    return process


def stop_yaneuraou(process):
    """やねうら王のプロセスを終了"""
    if process:
        process.terminate()
        process.wait()

def send_command(process, command):
    """やねうら王にコマンドを送信"""
    process.stdin.write(command + "\n")
    process.stdin.flush()


def read_output(process, response_queue):
    """ やねうら王の応答を非同期で読みとる関数 """
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"やねうら王の応答: {output.strip()}")
            if any(keyword in output for keyword in ["readyok", "bestmove", "multipv", "Error", "mate", "info"]):
                response_queue.append(output.strip())


def initialize_yaneuraou(process, response_queue):
    """やねうら王の初期化コマンドを送信"""
    initial_commands = ["usi", "isready", "usinewgame"]
    for command in initial_commands:
        send_command(process, command)
        time.sleep(0.5)  # 応答を待つ時間
    # 応答キューに "readyok" が来るまで待機
    while "readyok" not in response_queue:
        time.sleep(0.1)
        
    response_queue.pop(0)
    