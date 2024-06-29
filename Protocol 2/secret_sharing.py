from random import randint


def eval_poly(coeffs, m, x):
    res = 0
    
    for i in range(len(coeffs) - 1, -1, -1):
        res = (coeffs[i] + x * res) % m
    
    return res


def make_shares(s, n, t, m):
    shares, coeffs = [], [s]
    
    for i in range(t - 1):
        coeffs.append(randint(0, m - 1))
    
    shares = [(i, eval_poly(coeffs, m, i)) for i in range(1, n + 1)]

    return shares, coeffs


def recover_secret(shares, m):
    secret = 0
    n = len(shares)

    xs = [share[0] for share in shares]
    
    for share in shares:
        i, y = share
        res = 1
        for j in xs:
            if j != i:
                res = (res * (-j % m)) % m
                denom = ((i - j) % m)**(m - 2) % m
                res = (res * denom) % m
        secret = (secret + y * res) % m
    
    return secret
