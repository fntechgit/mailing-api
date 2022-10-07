from abc import abstractmethod


class MaintenanceService:

    @abstractmethod
    def purge(self, older_than_days: int):
        pass
