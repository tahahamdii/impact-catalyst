FROM python:3.11

RUN mkdir /climate-and-gender-ai

WORKDIR /climate-and-gender-ai

COPY . /climate-and-gender-ai

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

