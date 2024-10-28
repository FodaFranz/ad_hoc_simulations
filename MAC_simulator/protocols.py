from dataclasses import dataclass
from random import randint
from typing import Protocol


@dataclass
class HighLevelMessage:
    target: int
    content: str
    length: int


@dataclass
class Message:
    """
    This message class is utilized by the protocol layer in order to communicate
    """
    target: int
    source: int
    sequence_number: int
    content: str
    length: int

    def get_ack(self):
        return Message(self.source, self.target, self.sequence_number, 'ack', 1)

class MACProtocol(Protocol):

    buffer: list
    backoff: int

    def generate_packet(self, message: HighLevelMessage):
        """
        This tells the protocol to generate a packet with the given message.
        The protocol then internally has to push the correct packet, like maybe an RTS into the sending queue

        :param message:
        :return:
        """

    def receive_packet(self, message: Message) -> None:
        """
        Parse incoming tranmission
        Checks if the transmission is relevant for this node.
        Schedules reply transmission into the send_buffer
        :return: Nothing
        """

    def send_packet(self) -> Message:
        """
        Keeps track of the back_off (gets called every idle tick), send_schedule, and buffer.
        Returns a transmission if it is time to send or as a reaction to a cts.
        Once sent the physical layer should immediately switch to a transmitting state.

        :return:
        """
        ...


class RTC_CTS_ALOHA:
    def __init__(self, identifier: int):
        self.id = identifier
        self.backoff = randint(1, 16)
        self.wait_counter = 0
        self.buffer: list[Message] = []
        self.message_buffer: dict[int: Message] = {}
        self.sequence_number = 0
        self.rts_lock = False # gets set to True after receiving a RTS

    def get_next_sequence_number(self):
        self.sequence_number += 1
        return self.sequence_number

    def generate_packet(self, message: HighLevelMessage):
        sequence = self.get_next_sequence_number()

        rts = Message(message.target, self.id, sequence, f'rts {message.length}', 1)
        self.buffer.append(rts)

        formatted_message = Message(message.target, self.id, sequence, message.content, message.length)
        self.message_buffer[sequence] = formatted_message

    def receive_packet(self, message: Message) -> None:

        # TODO still need to increase the backoff /
        # ignoring by this, note that back-off is already paused due to node state machine
        if message.target != self.id:
            print(f'node {self.id}: receive_packet: Discarded {message}')

            if 'rts' in message.content:
                print(f'\tnode {self.id}: receive_packet: Ignore RTS')
                self.wait_counter = 15 # TODO: change hardcoded value to something useful
                return
            
            if 'cts' in message.content:
                print(f'\tnode {self.id}: receive_packet: Ignore CTS')
                self.wait_counter = 50 # TODO: change hardcoded value to something useful
                return

            return
        # technically a message needs a sequence number,
        # in theory a stray ack might now delete a random message in the buffer

        print(f'node {self.id}: receive_packet: Received {message}')

        # whilst awaiting a reply we ignore all incoming rts requests.
        if 'rts' in message.content and not self.wait_counter and not self.rts_lock:
            print(f'\tnode {self.id}: receive_packet: Received RTS. Add CTS to buffer')
            self.backoff = 0
            self.buffer.insert(0, Message(message.source, message.target, message.sequence_number, f'cts {message.length}', 1))
            self.rts_lock = True
            return

        if 'cts' in message.content:
            print(f'\tnode {self.id}: receive_packet: Received CTS. Add data to buffer')
            # while technically not an ack it is an ack towards the last sent rts message.
            self.wait_counter = 0
            self.backoff = 0
            self.buffer.insert(0, self.message_buffer[message.sequence_number])
            return

        if self.buffer and message.source == self.buffer[0].target and message.content == 'ack' and message.sequence_number == self.buffer[0].sequence_number:
            print(f'\tnode {self.id}: receive_packet: Received ACK. Delete RTS from buffer')
            self.wait_counter = 0
            del self.buffer[0]  # deletes the RTS message from the buffer.
            return

        # in all other scenarios it was a message intended for us so we push an ack to the buffer
        if 'cts' not in message.content and 'rts' not in message.content and 'ack' not in message.content:
            # this now just assumes that we got a data packet and we reply with an ack.
            print(f'\tnode {self.id}: receive_packet: Received data. Add ACK to buffer')
            self.buffer.insert(0, message.get_ack())
            self.wait_counter = 0
            self.backoff = 0
            return

        print(f'node {self.id}: receive_packet:stray and ignored packet arrived')

    def send_packet(self) -> Message:
        # if awaiting an ack we should pause the whole system
        if self.wait_counter:
            self.wait_counter -= 1
            return
        
        # Check if we want to send something
        if not self.buffer:
            return

        self.backoff = max(0, self.backoff-1)
        if self.backoff == 0:
            self.backoff = randint(1, 16)
            self.wait_counter = 50 

            # no packet should be stored in the buffer apart from rts packets which will trigger new packets in the buffer.
            # so we delete this from the buffer upon transmission
            transmission = self.buffer[0]
            if 'rts' not in transmission.content:
                del self.buffer[0]
            if 'cts' in transmission.content:
                self.rts_lock = False

            if 'ack' in transmission.content:
                self.wait_counter = 0  # after an ack we do not await anything anymore.

            print("node {}: send_packet: {}".format(self.id, transmission))

            return transmission

class ALOHA:
    def __init__(self, identifier: int):
        self.id = identifier
        self.backoff = randint(1, 16)
        self.wait_counter = 0
        self.buffer: list[Message] = []
        self.sequence_number = 0

    def get_next_sequence_number(self):
        self.sequence_number += 1
        return self.sequence_number

    def generate_packet(self, message: HighLevelMessage):
        message = Message(message.target, self.id, self.get_next_sequence_number(), message.content, message.length)
        self.buffer.append(message)

    def receive_packet(self, message: Message) -> None:
        if message.target != self.id:
            return
        # technically a message needs a sequence number,
        # in theory a stray ack might now delete a random message in the buffer
        if self.buffer and message.source == self.buffer[0].target and message.content == 'ack' and message.sequence_number == self.buffer[0].sequence_number:
            print(f'{self.id} received ack')
            self.wait_counter = 0
            del self.buffer[0]
            return

        # in all other scenarios it was a message intended for us so we push an ack to the buffer
        print(f'{self.id} pushing ack to buffer')
        self.buffer.insert(0, message.get_ack())
        self.backoff = 0

    def send_packet(self) -> Message:
        # if awaiting an ack we should pause the whole system
        if self.wait_counter:
            self.wait_counter -= 1
            return
        if not self.buffer:
            return

        self.backoff = max(0, self.backoff-1)
        if self.backoff == 0:
            self.backoff = randint(1, 16)
            self.wait_counter = 50
            return self.buffer[0]
