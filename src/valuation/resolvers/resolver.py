from pydantic import BaseModel


class Resolvers(BaseModel):
    """
    Unified container for a complete valuation session's inputs.

    This model follows the 'Ghost Architecture' where fields start as None
    to allow for a traceable resolution between User, Provider, and Fallback.
    """
    common: CommonResolvers
    strategy: StrategyUnionResolvers
    extensions: ExtensionBundleResolvers