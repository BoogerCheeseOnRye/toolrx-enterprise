from setuptools import setup, find_packages

setup(
    name="toolrx",
    version="1.0.0",
    description="Deterministic micro tool router for LLM/agent calling with zero LLM dependency.",
    author="ToolRx Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[],
    entry_points={
        "console_scripts": [
            "toolrx-gateway=toolrx.gateway.server:ToolRxGatewayServer",
        ],
    },
)
