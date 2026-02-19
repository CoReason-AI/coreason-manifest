import idna

def canonicalize_domain(domain: str) -> str:
    """
    Canonicalizes a domain name for strict comparison.
    1. Strips trailing dot.
    2. Lowercases.
    3. IDNA encodes to ASCII (Punycode) using strict IDNA 2008 rules.
    """
    if not domain:
        return ""

    # 1. Strip trailing dot
    domain = domain.rstrip(".")

    # 2. Lowercase (for IDNA pre-processing)
    domain = domain.lower()

    try:
        # 3. IDNA Encode
        # idna.encode returns bytes, we decode to ascii string
        return str(idna.encode(domain).decode("ascii"))
    except idna.IDNAError:
        # If encoding fails, it's likely an invalid domain.
        # We return the lowercased version but it won't be punycode.
        return domain
