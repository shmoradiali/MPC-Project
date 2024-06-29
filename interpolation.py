def interpolate(shares, t, p):
    secret = 0
    t = len(shares)

    xs = [i for i in range(1, t + 1)]

    for k, share in enumerate(shares):
        y = share
        i = k + 1
        res = 1
        for j in xs:
            if j != i:
                res = (res * (-j % p)) % p
                denom = ((i - j) % p) ** (p - 2) % p
                res = (res * denom) % p
        secret = (secret + y * res) % p

    return secret

