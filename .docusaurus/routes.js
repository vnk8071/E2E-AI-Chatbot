import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug', '2a7'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug/config',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug/config', '504'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug/content',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug/content', '161'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug/globalData',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug/globalData', 'bc9'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug/metadata',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug/metadata', 'c15'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug/registry',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug/registry', 'a90'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/__docusaurus/debug/routes',
    component: ComponentCreator('/e2e-ai-chatbot/__docusaurus/debug/routes', '63e'),
    exact: true
  },
  {
    path: '/e2e-ai-chatbot/docs',
    component: ComponentCreator('/e2e-ai-chatbot/docs', '849'),
    routes: [
      {
        path: '/e2e-ai-chatbot/docs/get-started',
        component: ComponentCreator('/e2e-ai-chatbot/docs/get-started', 'cd9'),
        exact: true,
        sidebar: "sideBar"
      },
      {
        path: '/e2e-ai-chatbot/docs/installation',
        component: ComponentCreator('/e2e-ai-chatbot/docs/installation', '9ca'),
        exact: true,
        sidebar: "sideBar"
      },
      {
        path: '/e2e-ai-chatbot/docs/introduction',
        component: ComponentCreator('/e2e-ai-chatbot/docs/introduction', 'f63'),
        exact: true,
        sidebar: "sideBar"
      }
    ]
  },
  {
    path: '/e2e-ai-chatbot/',
    component: ComponentCreator('/e2e-ai-chatbot/', '880'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
