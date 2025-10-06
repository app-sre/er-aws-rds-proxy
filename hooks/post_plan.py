#!/usr/bin/env python3

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from botocore.exceptions import ClientError
from external_resources_io.config import Config
from external_resources_io.input import parse_model, read_input_from_file
from external_resources_io.log import setup_logging
from external_resources_io.terraform import (
    Action,
    ResourceChange,
    TerraformJsonPlanParser,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

from er_aws_rds_proxy.app_interface_input import AppInterfaceInput
from hooks_lib.aws_api import AWSApi

logger = logging.getLogger(__name__)


class RdsProxyPlanValidator:
    """The plan validator class"""

    def __init__(
        self, plan: TerraformJsonPlanParser, app_interface_input: AppInterfaceInput
    ) -> None:
        self.plan = plan
        self.input = app_interface_input
        self.aws_api = AWSApi(config_options={"region_name": self.input.data.region})
        self.errors: list[str] = []

    @property
    def rds_proxy_instance_updates(self) -> list[ResourceChange]:
        """Get the rds proxy instance updates"""
        return [
            c
            for c in self.plan.plan.resource_changes
            if c.type == "aws_db_proxy"
            and c.change
            and Action.ActionCreate in c.change.actions
        ]

    def _validate_subnets_and_return_vpc_id(self, subnets: Sequence[str]) -> str | None:
        logger.info(f"Validating subnets {subnets}")

        vpc_ids: set[str] = set()

        try:
            data = self.aws_api.get_subnets(subnets)
        except ClientError as e:
            self.errors.append(f"Error validating subnets: {e}")
            return None

        if missing := set(subnets).difference({s.get("SubnetId") for s in data}):
            self.errors.append(f"Subnet(s) {missing} not found")
            return None

        for subnet in data:
            if "VpcId" not in subnet:
                self.errors.append(
                    f"VpcId not found for subnet {subnet.get('SubnetId')}"
                )
                continue
            vpc_ids.add(subnet["VpcId"])

        if len(vpc_ids) > 1:
            self.errors.append("All subnets must belong to the same VPC")

        return vpc_ids.pop() if vpc_ids else None

    def _validate_security_groups(
        self, security_groups: Sequence[str], vpc_id: str
    ) -> None:
        logger.info(f"Validating security group {security_groups}")
        try:
            data = self.aws_api.get_security_groups(security_groups)
        except ClientError as e:
            self.errors.append(f"Error validating security groups: {e}")
            return

        if missing := set(security_groups).difference({s.get("GroupId") for s in data}):
            self.errors.append(f"Security group(s) {missing} not found")
            return

        for sg in data:
            if sg.get("VpcId") != vpc_id:
                self.errors.append(
                    f"Security group {sg.get('GroupId')} does not belong to the same VPC as the subnets"
                )

    def validate(self) -> bool:
        """Validate method"""
        for u in self.rds_proxy_instance_updates:
            if not u.change or not u.change.after:
                continue

            if vpc_id := self._validate_subnets_and_return_vpc_id(
                subnets=u.change.after["vpc_subnet_ids"]
            ):
                self._validate_security_groups(
                    security_groups=u.change.after["vpc_security_group_ids"],
                    vpc_id=vpc_id,
                )
        return not self.errors


if __name__ == "__main__":
    setup_logging()
    app_interface_input = parse_model(AppInterfaceInput, read_input_from_file())
    logger.info("Running RDS Proxy terraform plan validation")
    plan = TerraformJsonPlanParser(plan_path=Config().plan_file_json)
    validator = RdsProxyPlanValidator(plan, app_interface_input)
    if not validator.validate():
        logger.error(validator.errors)
        sys.exit(1)

    logger.info("Validation ended succesfully")
