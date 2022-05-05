
class Simulator:
    def __init__(self,initialState,script):
        self.state = initialState
        self.script = script

    def performTurn(self):
        shouldContinue = self.__performScriptedAction()
        if not shouldContinue:
            return
        pass

    def __performScriptedAction(self):
        pass