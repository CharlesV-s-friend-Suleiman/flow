from cistar.envs.loop import LoopEnvironment
from cistar.core import rewards

from rllab.spaces import Box
from rllab.spaces import Product

import traci

import numpy as np
from numpy.random import normal

import pdb


class SimpleAccelerationEnvironment(LoopEnvironment):
    """
    Fully functional environment. Takes in an *acceleration* as an action. Reward function is negative norm of the
    difference between the velocities of each vehicle, and the target velocity. State function is a vector of the
    velocities for each vehicle.
    """

    @property
    def action_space(self):
        """
        Actions are a set of accelerations from 0 to 15m/s
        :return:
        """
        return Box(low=-np.abs(self.env_params["max-deacc"]), high=self.env_params["max-acc"],
                   shape=(self.scenario.num_rl_vehicles, ))

    @property
    def observation_space(self):
        """
        See parent class
        An observation is an array the velocities for each vehicle
        """
        speed = Box(low=0, high=np.inf, shape=(self.scenario.num_vehicles,))
        absolute_pos = Box(low=0., high=np.inf, shape=(self.scenario.num_vehicles,))
        return Product([speed, absolute_pos])

        # # partial observability
        # speed = Box(low=0, high=np.inf, shape=(3,))
        # absolute_pos = Box(low=0., high=np.inf, shape=(3,))
        # return Product([speed, absolute_pos])

    def apply_rl_actions(self, rl_actions):
        """
        See parent class
        """
        sorted_rl_ids = [veh_id for veh_id in self.sorted_ids if veh_id in self.rl_ids]

        self.apply_acceleration(sorted_rl_ids, rl_actions)

    def compute_reward(self, state, rl_actions, **kwargs):
        """
        See parent class
        """
        reward = rewards.desired_velocity(
            state, rl_actions, fail=kwargs["fail"], target_velocity=self.env_params["target_velocity"])

        # # global reward function for partial observability
        # vel = np.array([self.vehicles[veh_id]["speed"] for veh_id in self.ids])
        # if any(vel < -100) or kwargs["fail"]:
        #     return 0.
        # max_cost = np.array([kwargs["target_velocity"]] * self.scenario.num_vehicles)
        # max_cost = np.linalg.norm(max_cost)
        # cost = vel - kwargs["target_velocity"]
        # cost = np.linalg.norm(cost)
        # reward = max(max_cost - cost, 0)

        return reward

    def getState(self, **kwargs):
        """
        See parent class
        The state is an array the velocities for each vehicle
        :return: a matrix of velocities and absolute positions for each vehicle
        """
        # return np.array([[self.vehicles[veh_id]["speed"] + normal(0, self.observation_vel_std),
        #                   self.vehicles[veh_id]["absolute_position"] + normal(0, self.observation_pos_std)]
        #                  for veh_id in self.sorted_ids]).T

        # # partial observability for stabilizing the ring
        # vehID = self.rl_ids[0]
        # lead_id = self.vehicles[vehID]["leader"]
        # trail_id = self.vehicles[vehID]["follower"]
        #
        # # state contains the speed of the rl car, and its leader and follower,
        # # as well as the rl car's position in the network, and its headway with the vehicles adjacent to it
        # observation = np.array([
        #     [self.vehicles[trail_id]["speed"], self.vehicles[vehID]["speed"],
        #      self.vehicles[lead_id]["speed"]],
        #     [self.vehicles[trail_id]["headway"], self.vehicles[vehID]["absolute_position"],
        #      self.vehicles[vehID]["headway"]]])
        # return observation

        # implicit labeling for stabilizing the ring (centering the rl vehicle, scaling and using relative position)
        indx_rl = np.where(["rl" in self.vehicles[veh_id]["id"] for veh_id in self.sorted_ids])[0]
        num_vehicles = self.scenario.num_vehicles
        ids_centering_rl = np.append(np.array([self.sorted_ids[i] for i in np.arange(indx_rl, num_vehicles)]),
                                     np.array([self.sorted_ids[i] for i in np.arange(indx_rl)]))

        scaled_rel_pos = [(self.vehicles[veh_id]["absolute_position"] % self.scenario.length) / self.scenario.length
                          for veh_id in ids_centering_rl]
        vel = [self.vehicles[veh_id]["speed"] for veh_id in ids_centering_rl]

        return np.array([[vel[i], scaled_rel_pos[i]] for i in range(len(ids_centering_rl))]).T

    def render(self):
        print('current state/velocity:', self.state)
