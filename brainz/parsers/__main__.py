import logging

import click
import pika
from furl import furl
from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from . import version, parse, get_parser, Parser

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s", datefmt="%d-%m-%y %H:%M:%S"
)

logger = logging.getLogger("parsers")


@click.group()
@click.version_option(version)
def cli():
    pass


@cli.command("parse")
@click.argument("parser")
@click.argument("snapshot", type=click.File("rb"))
def parse_data(parser, snapshot):
    """
    Call PARSER with the data from SNAPSHOT and print the result.
    """
    click.echo(parse(parser, snapshot.read()))


@cli.command("run-parser")
@click.argument("parser")
@click.argument("message_queue_url")
def run_parser(parser, message_queue_url):
    """
    Run PARSER on data from MESSAGE_QUEUE_URL.
    """
    consume(message_queue_url, get_parser(parser))


def consume(url: str, parser: Parser) -> None:
    """
    Consume messages from the message queue on the given url.

    :param url: The url of the message queue.
    :param parser: The method to use on each received message.
    """
    url = furl(url)
    if url.scheme == "rabbitmq":
        consume_rmq(url.host, url.port, parser)
    else:
        raise NotImplementedError(f"Not supported scheme {url.scheme}")


def consume_rmq(host: str, port: int, parser: Parser):
    """
    Consume messages from the `snapshots` exchange on the given RabbitMQ host.

    :param host: The RabbitMQ host.
    :param port: The RabbitMQ port.
    :param parser: The method to use on each received message.
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port))
    channel = connection.channel()
    channel.exchange_declare(exchange="snapshots", exchange_type="fanout")
    queue_name = channel.queue_declare(queue="", exclusive=True).method.queue
    channel.queue_bind(exchange="snapshots", queue=queue_name)

    channel.exchange_declare(exchange="parsers_data", exchange_type="topic")

    def callback(ch: Channel, method: Basic.Deliver, properties: BasicProperties, message: bytes) -> None:
        parsed = parser.parse(message)
        ch.basic_publish(exchange="parsers_data", routing_key=parser.name, body=parsed)
        logger.info("Published message")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    logger.info(f"Starting consuming for parser {parser.name}")

    channel.start_consuming()


if __name__ == "__main__":
    cli(prog_name="brainz.parsers")
