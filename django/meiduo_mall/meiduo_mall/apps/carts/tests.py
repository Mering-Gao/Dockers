import pickle, base64

# Create your tests here.
if __name__ == '__main__':

    dict = {
        'name':'zs',
        'age':123,
        'age1':123,
        'age2':123,
        'age3':123,
        'age4':123,
        'age5':123,
        'age6':123,
        'age7':123,
        'age8':123,
    }

    # data_bytes = pickle.dumps(dict)
    # print(data_bytes)
    #
    #
    #
    # result = base64.b64encode(data_bytes)
    # print(result)
    #
    #
    # result1 = result.decode()
    # print(result1)

    # 加密:
    result1 = base64.b64encode(pickle.dumps(dict)).decode()

    # 解密:
    data = pickle.loads(base64.b64decode(result1))
    print(data)





    # data = pickle.loads(data_bytes)
    # print(data)
