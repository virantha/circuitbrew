import circuitbrew.circuitbrew as P

import pytest
import os
import logging

import smtplib
from mock import Mock
from mock import patch, call
from mock import MagicMock
from mock import PropertyMock


class Testcircuitbrew:

    def setup(self):
        self.p = P.CircuitBrew()

    def test_big(self):
        #self.p.get_options(['-v', 'n7.sp', 'circuitbrew.examples.simple3', 'hspice', ])
        self.p.techfile = 'n7.sp'
        self.p.module = 'circuitbrew.examples.simple3'
        self.p.netlist_type = 'hspice'
        sp = self.p.netlist()
        print(sp)

