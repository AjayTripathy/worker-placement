"""Connector modules — one per M source.

Each connector implements `BaseConnector` from `.base` and exposes a
`query(request: ConnectorRequest) -> ConnectorResult` method. The dispatcher
loads them dynamically by module path declared in the source atlas.
"""
