class Iterable():
    def __init__(self) -> None:
        self._current = 0
    def __len__(self):
        pass
    def __iter__(self):
        return self
    def __next__(self):
        if self._current >= self.__len__():
            raise StopIteration
        index = self._current
        self._current+=1
        return self.__getitem__(index)
    def __getitem__(self,index:int):
        pass