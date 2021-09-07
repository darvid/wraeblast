class WraeblastError(Exception):
    ...


class InsightsError(WraeblastError):
    ...


class UnsuccessfulInsightsRequest(InsightsError):
    ...
