from chatcli import *
from threading import Thread


import flet as ft


TARGET_IP = os.getenv("SERVER_IP") or "127.0.0.1"
TARGET_PORT = os.getenv("SERVER_PORT") or "8889"
ON_WEB = os.getenv("ONWEB") or "0"


def main(page):
    def client_received():
        while True:
            message = cc.sock.recv(1024).decode()
            if message != 'exit':
                lv.controls.append(ft.Text(
                    f"{message}",
                    color = ft.colors.ORANGE
                ))
                page.update()
            else:
                cmd.label = 'Your command'
                lv.controls.append(ft.Text(
                    f"Telah keluar dari grup",
                    color = ft.colors.RED
                ))
                page.update()
                break

    def client_send(e):
        chat = cmd.value
        cc.sock.sendall(chat.encode())
        cmd.value=""
        if chat=='exit':
            btn.on_click=btn_click
        page.update()

    def btn_click(e):
        if not cmd.value:
            cmd.error_text = "masukkan command"
            page.update()
        else:
            txt = cmd.value
            lv.controls.append(ft.Text(f"command: {txt}"))
            txt = cc.proses(txt)
            if txt == 'masuk':
                cmd.value=''

                receiveThread = Thread(target=client_received, args=())
                receiveThread.start()
                cmd.label = 'Kirim pesan ke grup'
                btn.on_click = client_send
                page.update()
            
            negative = ['Maaf', 'Error']

            if any(word in txt for word in negative):
                lv.controls.append(ft.Text(
                    f"result {cc.tokenid}: {txt}",
                    color = ft.colors.RED
                ))
            else:
                lv.controls.append(ft.Text(
                    f"result {cc.tokenid}: {txt}",
                    color = ft.colors.GREEN
                ))

            cmd.value=""
            page.update()


    cc = ChatClient()

    lv = ft.ListView(expand=1, spacing=10, padding=20, auto_scroll=True)
    cmd = ft.TextField(label="Your command")

    page.add(lv)
    btn = ft.ElevatedButton("Send", on_click=btn_click)
    page.add(cmd, btn)


if __name__=='__main__':
    if (ON_WEB=="1"):
        ft.app(target=main,view=ft.WEB_BROWSER,port=8550)
    else:
        ft.app(target=main)

