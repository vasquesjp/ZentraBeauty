from urllib.parse import quote

def gerar_link_whatsapp(telefone, mensagem):
    """
    Gera o link da API do WhatsApp para ser usado nos botões da interface Web.
    """
    # Remove caracteres não numéricos
    numero_limpo = ''.join(filter(str.isdigit, telefone))
    
    # Se não tiver código do país, assume Brasil (+55)
    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"
        
    texto_codificado = quote(mensagem)
    
    # Retorna apenas o link pronto
    return f"https://api.whatsapp.com/send?phone={numero_limpo}&text={texto_codificado}"