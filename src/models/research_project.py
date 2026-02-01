from pydantic import BaseModel, Field

class ResearchProject(BaseModel):
    """
    Represents an active research project for a faction.
    Tracks progress towards unlocking a technology.
    """
    tech_id: str
    total_cost: int = Field(..., gt=0)
    progress: int = Field(0, ge=0)
    
    @property
    def remaining_cost(self) -> int:
        return max(0, self.total_cost - self.progress)
    
    @property
    def is_complete(self) -> bool:
        return self.progress >= self.total_cost

    def invest(self, amount: int) -> int:
        """
        Invests RP into the project.
        Returns the amount of overflow if completed.
        """
        needed = self.remaining_cost
        invested = min(amount, needed)
        self.progress += invested
        return amount - invested
