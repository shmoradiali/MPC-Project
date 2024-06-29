class Circuit:
    def __init__(self, n) -> None:
        self.n = n
        self.gates = []
    
    def add(self, g1, g2):
        self.gates.append(('+', g1, g2))
    
    def multiply(self, g1, g2):
        self.gates.append(('*', g1, g2))
    
    def scale(self, c, g1):
        self.gates.append(('c', c, g1))
    
    def compute(self, xs):
        results = [x for x in xs]
        for i, g in enumerate(self.gates):
            t, g1, g2 = g
            if t == '+':
                results.append(results[g1] + results[g2])
            elif t == '*':
                results.append(results[g1] * results[g2])
            elif t == 'c':
                results.append(results[g2] * g1)
        
        return results[-1]


def lin_comb(coeffs, n):
    c = Circuit(n)

    for i in range(n):
        c.scale(coeffs[i], i)

    c.add(n, n + 1)
    out = 2 * n
    for i in range(2, n):
        c.add(n + i, out)
        out += 1
    
    return c
