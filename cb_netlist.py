import circuitbrew.circuitbrew as cb
import sys

if __name__=='__main__':
    script = cb.CircuitBrew()
    script.go(sys.argv[1:])

