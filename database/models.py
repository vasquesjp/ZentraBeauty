from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.now)
    status = Column(String, default="A")
    aniversario = Column(Date, nullable=True)
    obs = Column(String(500), nullable=True) # <--- CAMPO NOVO PARA OBSERVACOES
    agendamentos = relationship("Agendamento", back_populates="cliente")

class Agendamento(Base):
    __tablename__ = 'agendamentos'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    data_hora = Column(DateTime, nullable=False)
    servico = Column(String, nullable=False)
    duracao_minutos = Column(Integer, default=120)
    status = Column(String, default="Pendente")
    
    cliente = relationship("Cliente", back_populates="agendamentos")

class Receita(Base):
    __tablename__ = 'receitas'
    id = Column(Integer, primary_key=True)
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=True)
    servico = Column(String)
    forma_pagamento = Column(String)
    status = Column(String, default="A")

class Despesa(Base):
    __tablename__ = 'despesas'
    id = Column(Integer, primary_key=True)
    valor = Column(Float, nullable=False)
    data = Column(Date, nullable=False)
    categoria = Column(String, nullable=False)
    descricao = Column(String)
    status = Column(String, default="A")

class Procedimento(Base):
    __tablename__ = 'procedimentos'
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    valor = Column(Float, nullable=False)
    categoria = Column(String) 
    percentual_manutencao = Column(Float, default=40.0) 
    status = Column(String, default="A")

class Foto(Base):
    __tablename__ = 'fotos'
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    imagem = Column(String, nullable=False)
    legenda = Column(String)