import tushare as ts


def main():
    pro = ts.pro_api()

    # 设置你的token
    df = pro.user(token='93aaf58e14cf4ca7c60001d604f65a22767c21b3e769e778e77cd2f2')

    print(df)


if __name__ == "__main__":
    main()