import okserver.okserver as ok


def main():
    pass


if __name__ == '__main__':
    server = ok.Server(main)
    server.start('', 2222)