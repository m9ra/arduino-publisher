import datetime
import logging
import traceback
from threading import Thread
from time import sleep

import serial.tools.list_ports
import unidecode as unidecode
from prometheus_client import REGISTRY, generate_latest, Gauge


class ArduinoReader(object):
    def __init__(self, log_limit=100):
        self._worker_thread = None
        self._log_limit = log_limit
        self._serial_monitor = []
        self._parsed_values = {}
        self._value_gauges = {}
        self._id = int(datetime.datetime.now().timestamp())
        self._is_connected = False

    @property
    def is_connected(self):
        return self._is_connected

    def start(self):
        if self._worker_thread is not None:
            raise AssertionError("Can't start twice")

        self._worker_thread = Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def get_serial_monitor(self):
        return list(self._serial_monitor)

    def get_parsed_values(self):
        return dict(self._parsed_values)

    def get_prometheus_metrics(self):
        return generate_latest(REGISTRY)

    def _worker(self):
        while True:
            try:
                port = self._find_serial_port()
                if port:
                    self._read(port)

            except:
                traceback.print_exc()

            finally:
                self._is_connected = False

            sleep(5)

    def _find_serial_port(self):
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            description = p.description.lower()
            if "ch340" in description or "arduino" in description or "usb serial" in description or "usb2.0-serial" in description:
                return p

        return None

    def _read(self, port_info):
        baudrate = 115200
        ser = serial.Serial(port=port_info.device, baudrate=baudrate)
        print(f"Connecting to {port_info} with baudrate={baudrate}")
        self._is_connected = True
        while ser.is_open:
            line_bytes = ser.readline()
            line = line_bytes.decode('utf8').strip()

            self._update_serial_monitor(line)
            self._update_parsed_values(line)

    def _update_parsed_values(self, line: str):
        parts = line.split(':', maxsplit=1)
        if len(parts) == 1:
            value = parts[0].strip()
            if not value:
                # ignore empty messages
                return

            field = "message"
        else:
            field, value = parts

        now = datetime.datetime.now()
        self._parsed_values[field] = {
            'field': field.strip(),
            'value': value.strip(),
            'updated_at': now.timestamp()
        }

        try:
            value_parts = value.split()
            for i in range(0, len(value_parts), 2):
                value_part = value_parts[i]
                current_field = field
                if i + 1 < len(value_parts):
                    current_field += ' ' + value_parts[i + 1]

                if current_field not in self._value_gauges:
                    field_name = current_field.replace('.', '_').replace(' ', '_').replace('°', 'degree').replace('%', 'percent')
                    field_name = unidecode.unidecode(field_name)
                    self._value_gauges[current_field] = Gauge(f"field_{field_name}", f'Value of the field `{current_field}`.')

                self._value_gauges[current_field].set(value_part)

        except:
            logging.exception("Prometheus metric parsing failed.")

        keys_to_delete = []
        for key, value in self._parsed_values.items():
            age = now.timestamp() - value['updated_at']
            if age > 3600:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            self._parsed_values.pop(key, None)
            self._value_gauges.pop(key, None)

    def _update_serial_monitor(self, line: str):
        now = datetime.datetime.now()
        self._id += 1
        self._serial_monitor.append({'line': line, 'time': now.timestamp(), 'id': self._id})
        while len(self._serial_monitor) > self._log_limit:
            self._serial_monitor.pop(0)
