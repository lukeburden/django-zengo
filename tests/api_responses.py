# -*- coding: utf-8 -*-

import json


new_ticket = json.loads(
    r"""{
  "ticket": {
    "url": "https://example.zendesk.com/api/v2/tickets/1.json",
    "id": 1,
    "external_id": null,
    "via": {
      "channel": "email",
      "source": {
        "from": {
          "address": "someone@example.com",
          "name": "Monica H."
        },
        "to": {
          "name": "Support",
          "address": "help@example.com"
        },
        "rel": null
      }
    },
    "created_at": "2019-01-13T20:25:33Z",
    "updated_at": "2019-01-15T03:09:32Z",
    "type": "incident",
    "subject": "Maintenance request",
    "raw_subject": "Maintenance request",
    "description": "This is the first comment of the ticket, effectively",
    "priority": "urgent",
    "status": "open",
    "recipient": "help@example.com",
    "requester_id": 1,
    "submitter_id": 2,
    "assignee_id": null,
    "organization_id": null,
    "group_id": null,
    "collaborator_ids": [
      1,
      2
    ],
    "follower_ids": [
      1,
      2
    ],
    "email_cc_ids": [],
    "forum_topic_id": null,
    "problem_id": null,
    "has_incidents": false,
    "is_public": true,
    "due_at": null,
    "tags": [
      "follow_up_sent",
      "maintenance",
      "portland"
    ],
    "custom_fields": [
      {
        "id": 1,
        "value": "donkey"
      },
      {
        "id": 2,
        "value": "tree"
      }
    ],
    "satisfaction_rating": {
      "score": "unoffered"
    },
    "sharing_agreement_ids": [],
    "fields": [
      {
        "id": 1,
        "value": "donkey"
      },
      {
        "id": 2,
        "value": "tree"
      }
    ],
    "followup_ids": [],
    "brand_id": 1,
    "allow_channelback": false,
    "allow_attachments": true
  }
}"""
)


requester = json.loads(
    r"""{
  "user": {
    "id": 1,
    "url": "https://example.zendesk.com/api/v2/users/1.json",
    "name": "Monica",
    "email": "monica@example.com",
    "created_at": "2019-01-10T22:06:54Z",
    "updated_at": "2019-01-11T00:01:37Z",
    "time_zone": "Arizona",
    "iana_time_zone": "America/Phoenix",
    "phone": null,
    "shared_phone_number": null,
    "photo": {
      "url": "https://example.zendesk.com/api/v2/attachments/360058277492.json",
      "id": 360058277492,
      "file_name": "IMG_5033.JPG",
      "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
      "mapped_content_url":"https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
      "content_type":"image/jpeg",
      "size":5999,
      "width":80,
      "height":68,
      "inline":false,
      "thumbnails": [
        {
          "url": "https://example.zendesk.com/api/v2/attachments/360058277512.json",
          "id": 360058277512,
          "file_name": "IMG_5033_thumb.JPG",
          "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
          "mapped_content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
          "content_type": "image/jpeg",
          "size": 1449,
          "width": 32,
          "height": 27,
          "inline": false
        }
      ]
    },
    "locale_id": 1,
    "locale": "en-US",
    "organization_id": null,
    "role": "end-user",
    "verified": false,
    "external_id": null,
    "tags": [],
    "alias": "",
    "active": true,
    "shared": false,
    "shared_agent": false,
    "last_login_at": null,
    "two_factor_auth_enabled": false,
    "signature": null,
    "details": "",
    "notes": "",
    "role_type": null,
    "custom_role_id": null,
    "moderator": false,
    "ticket_restriction": "requested",
    "only_private_comments": false,
    "restricted_agent": true,
    "suspended": false,
    "chat_only": false,
    "default_group_id": null,
    "report_csv": false,
    "user_fields": {}
  }
}
"""
)

submitter = json.loads(
    r"""{
  "user": {
    "id": 2,
    "url": "https://example.zendesk.com/api/v2/users/2.json",
    "name": "Submitter",
    "email": "submitter@example.com",
    "created_at": "2019-01-10T22:06:54Z",
    "updated_at": "2019-01-11T00:01:37Z",
    "time_zone": "Arizona",
    "iana_time_zone": "America/Phoenix",
    "phone": null,
    "shared_phone_number": null,
    "photo": {
      "url": "https://example.zendesk.com/api/v2/attachments/360058277492.json",
      "id": 360058277492,
      "file_name": "IMG_5033.JPG",
      "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
      "mapped_content_url":"https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
      "content_type":"image/jpeg",
      "size":5999,
      "width":80,
      "height":68,
      "inline":false,
      "thumbnails": [
        {
          "url": "https://example.zendesk.com/api/v2/attachments/360058277512.json",
          "id": 360058277512,
          "file_name": "IMG_5033_thumb.JPG",
          "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
          "mapped_content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
          "content_type": "image/jpeg",
          "size": 1449,
          "width": 32,
          "height": 27,
          "inline": false
        }
      ]
    },
    "locale_id": 1,
    "locale": "en-US",
    "organization_id": null,
    "role": "end-user",
    "verified": false,
    "external_id": null,
    "tags": [],
    "alias": "",
    "active": true,
    "shared": false,
    "shared_agent": false,
    "last_login_at": null,
    "two_factor_auth_enabled": false,
    "signature": null,
    "details": "",
    "notes": "",
    "role_type": null,
    "custom_role_id": null,
    "moderator": false,
    "ticket_restriction": "requested",
    "only_private_comments": false,
    "restricted_agent": true,
    "suspended": false,
    "chat_only": false,
    "default_group_id": null,
    "report_csv": false,
    "user_fields": {}
  }
}
"""
)

no_comments = json.loads(
    r"""{
  "comments": [],
  "next_page": null,
  "previous_page": null,
  "count": 0
}
"""
)

one_comment = json.loads(
    r"""{
  "comments": [
    {
      "id": 1,
      "type": "Comment",
      "author_id": 1,
      "body": "Hello - could use your help!",
      "html_body": "An awful long string of HTML<div></div>",
      "plain_body": "Hello - could use your help!",
      "public": true,
      "attachments": [],
      "audit_id": 1,
      "via": {
        "channel": "email",
        "source": {
          "from": {
            "address": "monica@example.com",
            "name": "Monica",
            "original_recipients": [
              "help@example.com"
            ]
          },
          "to": {
            "name": "Support",
            "address": "help@example.com"
          },
          "rel": null
        }
      },
      "created_at": "2019-01-13T20:25:33Z",
      "metadata": {
        "system": {
          "message_id": "<5c3b9e5ebd2c3_244772acf2f0932a080d8@combo1>",
          "ip_address": "127.0.0.1",
          "raw_email_identifier": "2277328/5c4b4cfd-5b1b-4864-b00a-1e42abe273d9.eml",
          "json_email_identifier": "2277328/5c4b4cfd-5b1b-4864-b00a-1e42abe273d9.json"
        },
        "custom": {},
        "suspension_type_id": null
      }
    }
  ],
  "next_page": null,
  "previous_page": null,
  "count": 1
}
"""
)

two_comments = json.loads(
    r"""{
  "comments": [
    {
      "id": 1,
      "type": "Comment",
      "author_id": 1,
      "body": "Hello - could use your help!",
      "html_body": "An awful long string of HTML<div></div>",
      "plain_body": "Hello - could use your help!",
      "public": true,
      "attachments": [],
      "audit_id": 1,
      "via": {
        "channel": "email",
        "source": {
          "from": {
            "address": "monica@example.com",
            "name": "Monica",
            "original_recipients": [
              "help@example.com"
            ]
          },
          "to": {
            "name": "Support",
            "address": "help@example.com"
          },
          "rel": null
        }
      },
      "created_at": "2019-01-13T20:25:33Z",
      "metadata": {
        "system": {
          "message_id": "<5c3b9e5ebd2c3_244772acf2f0932a080d8@combo1>",
          "ip_address": "127.0.0.1",
          "raw_email_identifier": "2277328/5c4b4cfd-5b1b-4864-b00a-1e42abe273d9.eml",
          "json_email_identifier": "2277328/5c4b4cfd-5b1b-4864-b00a-1e42abe273d9.json"
        },
        "custom": {},
        "suspension_type_id": null
      }
    },
    {
      "id": 2,
      "type": "Comment",
      "author_id": 2,
      "body": "Hi Monica,\n\nThank you for reaching out to the team and bringing this to our attention.\n\nKaela\nSupporter\nExample Inc.",
      "html_body": "Comment 2 body with tons of HTML HTML HTML <strong>HOoooo</strong>",
      "plain_body": "Hi Monica,\n\nThank you for reaching out to the team and bringing this to our attention.\n\nKaela\nSupporter\nExample Inc.",
      "public": true,
      "attachments": [],
      "audit_id": 2,
      "via": {
        "channel": "web",
        "source": {
          "from": {},
          "to": {},
          "rel": null
        }
      },
      "created_at": "2019-01-13T20:30:41Z",
      "metadata": {
        "system": {
          "client": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
          "ip_address": "127.0.0.1",
          "location": "Wilmington, NC, United States",
          "latitude": 34.30,
          "longitude": -77.8
        },
        "custom": {}
      }
    }
  ],
  "next_page": null,
  "previous_page": null,
  "count": 2
}
"""
)

one_comment_with_attachments = json.loads(
    r"""{
  "comments": [
    {
      "id": 583514996211,
      "type": "Comment",
      "author_id": 1,
      "body": "Hi there Luke.​\n\nHere is an inline image.\n\n ![](https://example.zendesk.com/attachments/token/jFGBxOznWMG8lWRXUt0DAi1UQ/?name=IMG_20190101_001154.jpg)​\n\nWowsers, there is also an image and another file attached to this ticket.",
      "html_body": "<div class=\"zd-comment\" dir=\"auto\">Hi there Luke.​<br><br>Here is an inline image.<br><br><img src=\"https://example.zendesk.com/attachments/token/jFGBxOznWMG8lWRXUt0DAi1UQ/?name=IMG_20190101_001154.jpg\" data-original-height=\"3024\" data-original-width=\"4032\" style=\"height: auto; width: 4032px\">​<br><br>Wowsers, there is also an image and another file attached to this ticket.<br><br><br>\n</div>",
      "plain_body": "Hi there Luke.​\n\nHere is an inline image.\n\n​\n\nWowsers, there is also an image and another file attached to this ticket.",
      "public": true,
      "attachments": [
        {
          "url": "https://example.zendesk.com/api/v2/attachments/365674118331.json",
          "id": 365674118331,
          "file_name": "IMG_20190101_001154.jpg",
          "content_url": "https://example.zendesk.com/attachments/token/jFGBxOznWMG8lWRXUt0DAi1UQ/?name=IMG_20190101_001154.jpg",
          "mapped_content_url": "https://example.zendesk.com/attachments/token/jFGBxOznWMG8lWRXUt0DAi1UQ/?name=IMG_20190101_001154.jpg",
          "content_type": "image/jpeg",
          "size": 2599824,
          "width": 4032,
          "height": 3024,
          "inline": true,
          "thumbnails": [
            {
              "url": "https://example.zendesk.com/api/v2/attachments/365674118571.json",
              "id": 365674118571,
              "file_name": "IMG_20190101_001154_thumb.jpg",
              "content_url": "https://example.zendesk.com/attachments/token/MFe8s8o4hbPI6suwHBdkvMWgV/?name=IMG_20190101_001154_thumb.jpg",
              "mapped_content_url": "https://example.zendesk.com/attachments/token/MFe8s8o4hbPI6suwHBdkvMWgV/?name=IMG_20190101_001154_thumb.jpg",
              "content_type": "image/jpeg",
              "size": 2694,
              "width": 80,
              "height": 60,
              "inline": false
            }
          ]
        },
        {
          "url": "https://example.zendesk.com/api/v2/attachments/365692390412.json",
          "id": 365692390412,
          "file_name": "download.jpg",
          "content_url": "https://example.zendesk.com/attachments/token/JzYm4m7TNc3ZXlbNhgZDC2ugs/?name=download.jpg",
          "mapped_content_url": "https://example.zendesk.com/attachments/token/JzYm4m7TNc3ZXlbNhgZDC2ugs/?name=download.jpg",
          "content_type": "image/jpeg",
          "size": 6339,
          "width": 242,
          "height": 208,
          "inline": false,
          "thumbnails": [
            {
              "url": "https://example.zendesk.com/api/v2/attachments/365692390492.json",
              "id": 365692390492,
              "file_name": "download_thumb.jpg",
              "content_url": "https://example.zendesk.com/attachments/token/aNdp5xiwsW2u96U7IaZApCdk5/?name=download_thumb.jpg",
              "mapped_content_url": "https://example.zendesk.com/attachments/token/aNdp5xiwsW2u96U7IaZApCdk5/?name=download_thumb.jpg",
              "content_type": "image/jpeg",
              "size": 1917,
              "width": 80,
              "height": 69,
              "inline": false
            }
          ]
        },
        {
          "url": "https://example.zendesk.com/api/v2/attachments/365692415672.json",
          "id": 365692415672,
          "file_name": "lyft-2019-02-24.pdf",
          "content_url": "https://example.zendesk.com/attachments/token/2AO6OpL1pdAn6ouPrG9CpLeky/?name=lyft-2019-02-24.pdf",
          "mapped_content_url": "https://example.zendesk.com/attachments/token/2AO6OpL1pdAn6ouPrG9CpLeky/?name=lyft-2019-02-24.pdf",
          "content_type": "application/pdf",
          "size": 622787,
          "width": null,
          "height": null,
          "inline": false,
          "thumbnails": []
        }
      ],
      "audit_id": 583514996171,
      "via": {
        "channel": "web",
        "source": {
          "from": {},
          "to": {},
          "rel": null
        }
      },
      "created_at": "2019-03-27T18:31:54Z",
      "metadata": {
        "system": {
          "client": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
          "ip_address": "24.84.172.37",
          "location": "Vancouver, BC, Canada",
          "latitude": 49.25999999999999,
          "longitude": -123.0398
        },
        "custom": {}
      }
    },
    {
      "id": 584081472972,
      "type": "Comment",
      "author_id": 2,
      "body": "That's great, Zendesk. Here is an image in a response via EMAIL:\n\n\n ![fuse.jpg](https://example.zendesk.com/attachments/token/EcuesBNtbQm3I3FLvuDP9kpUK/?name=fuse.jpg)\n\n\n\nHope that helps.",
      "html_body": "<div class=\"zd-comment zd-comment-pre-styled\" dir=\"auto\">\n<div dir=\"ltr\">That's great, Zendesk. Here is an image in a response via EMAIL:<br><br><div>\n<img src=\"https://example.zendesk.com/attachments/token/EcuesBNtbQm3I3FLvuDP9kpUK/?name=fuse.jpg\" alt=\"fuse.jpg\" width=\"538\" height=\"303\"><br>\n</div>\n<div><br></div>\n<div>Hope that helps.</div>\n</div>\n<br>\n</div>",
      "plain_body": "That's great, Zendesk. Here is an image in a response via EMAIL:\n\n \n\n\n \n \n \n Hope that helps.",
      "public": true,
      "attachments": [
        {
          "url": "https://example.zendesk.com/api/v2/attachments/365692692292.json",
          "id": 365692692292,
          "file_name": "fuse.jpg",
          "content_url": "https://example.zendesk.com/attachments/token/EcuesBNtbQm3I3FLvuDP9kpUK/?name=fuse.jpg",
          "mapped_content_url": "https://example.zendesk.com/attachments/token/EcuesBNtbQm3I3FLvuDP9kpUK/?name=fuse.jpg",
          "content_type": "image/jpeg",
          "size": 48754,
          "width": null,
          "height": null,
          "inline": true,
          "thumbnails": [
            {
              "url": "https://example.zendesk.com/api/v2/attachments/365674480751.json",
              "id": 365674480751,
              "file_name": "fuse_thumb.jpg",
              "content_url": "https://example.zendesk.com/attachments/token/BvMqGiqQg9t1Kt8egzlmz87l4/?name=fuse_thumb.jpg",
              "mapped_content_url": "https://example.zendesk.com/attachments/token/BvMqGiqQg9t1Kt8egzlmz87l4/?name=fuse_thumb.jpg",
              "content_type": "image/jpeg",
              "size": 1588,
              "width": 80,
              "height": 45,
              "inline": false
            }
          ]
        }
      ],
      "audit_id": 584081472852,
      "via": {
        "channel": "email",
        "source": {
          "from": {
            "address": "monica@example.com",
            "name": "Monica",
            "original_recipients": [
              "monica@example.com",
              "support+id1@example.zendesk.com"
            ]
          },
          "to": {
            "name": "Example Org",
            "address": null
          },
          "rel": null
        }
      },
      "created_at": "2019-03-27T18:42:53Z",
      "metadata": {
        "system": {
          "message_id": "<CALzA2rnDc9AY8btg3yHqNt=j2QT1jKvehZO=P7e3fGWvM=CeHg@mail.gmail.com>",
          "raw_email_identifier": "2277328/9aa60a41-3a16-49c1-b126-92e4524fd7d3.eml",
          "json_email_identifier": "2277328/9aa60a41-3a16-49c1-b126-92e4524fd7d3.json"
        },
        "custom": {},
        "suspension_type_id": null
      }
    }
  ],
  "next_page": null,
  "previous_page": null,
  "count": 2
}
  """
)

search_one_result = json.loads(
    r"""{
  "results": [
    {
      "id": 1,
      "name": "Monica",
      "email": "monica@example.com",
      "created_at": "2019-01-10T22:06:54Z",
      "updated_at": "2019-01-11T00:01:37Z",
      "time_zone": "Arizona",
      "iana_time_zone": "America/Phoenix",
      "phone": null,
      "shared_phone_number": null,
      "photo": {
        "url": "https://example.zendesk.com/api/v2/attachments/360058277492.json",
        "id": 360058277492,
        "file_name": "IMG_5033.JPG",
        "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
        "mapped_content_url":"https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
        "content_type":"image/jpeg",
        "size":5999,
        "width":80,
        "height":68,
        "inline":false,
        "thumbnails": [
          {
            "url": "https://example.zendesk.com/api/v2/attachments/360058277512.json",
            "id": 360058277512,
            "file_name": "IMG_5033_thumb.JPG",
            "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
            "mapped_content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
            "content_type": "image/jpeg",
            "size": 1449,
            "width": 32,
            "height": 27,
            "inline": false
          }
        ]
      },
      "locale_id": 1,
      "locale": "en-US",
      "organization_id": null,
      "role": "end-user",
      "verified": false,
      "external_id": 1,
      "tags": [],
      "alias": "",
      "active": true,
      "shared": false,
      "shared_agent": false,
      "last_login_at": null,
      "two_factor_auth_enabled": false,
      "signature": null,
      "details": "",
      "notes": "",
      "role_type": null,
      "custom_role_id": null,
      "moderator": false,
      "ticket_restriction": "requested",
      "only_private_comments": false,
      "restricted_agent": true,
      "suspended": false,
      "chat_only": false,
      "default_group_id": null,
      "report_csv": false,
      "user_fields": {},
      "result_type": "user"
    }
  ],
  "facets": null,
  "next_page": null,
  "previous_page": null,
  "count": 1
}"""
)

search_no_results = json.loads(
    r"""{"results":[],"facets":null,"next_page":null,"previous_page":null,"count":0}"""
)

create_user_result = json.loads(
    r"""{
  "user": {
      "id": 1,
      "name": "Monica",
      "email": "monica@example.com",
      "created_at": "2019-01-10T22:06:54Z",
      "updated_at": "2019-01-11T00:01:37Z",
      "time_zone": "Arizona",
      "iana_time_zone": "America/Phoenix",
      "phone": null,
      "shared_phone_number": null,
      "photo": {
        "url": "https://example.zendesk.com/api/v2/attachments/360058277492.json",
        "id": 360058277492,
        "file_name": "IMG_5033.JPG",
        "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
        "mapped_content_url":"https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033.JPG",
        "content_type":"image/jpeg",
        "size":5999,
        "width":80,
        "height":68,
        "inline":false,
        "thumbnails": [
          {
            "url": "https://example.zendesk.com/api/v2/attachments/360058277512.json",
            "id": 360058277512,
            "file_name": "IMG_5033_thumb.JPG",
            "content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
            "mapped_content_url": "https://example.zendesk.com/system/photos/3600/5827/7492/IMG_5033_thumb.JPG",
            "content_type": "image/jpeg",
            "size": 1449,
            "width": 32,
            "height": 27,
            "inline": false
          }
        ]
      },
      "locale_id": 1,
      "locale": "en-US",
      "organization_id": null,
      "role": "end-user",
      "verified": false,
      "external_id": 1,
      "tags": [],
      "alias": "",
      "active": true,
      "shared": false,
      "shared_agent": false,
      "last_login_at": null,
      "two_factor_auth_enabled": false,
      "signature": null,
      "details": "",
      "notes": "",
      "role_type": null,
      "custom_role_id": null,
      "moderator": false,
      "ticket_restriction": "requested",
      "only_private_comments": false,
      "restricted_agent": true,
      "suspended": false,
      "chat_only": false,
      "default_group_id": null,
      "report_csv": false,
      "user_fields": {}
    }
}"""
)


create_user_dupe = json.loads(
    """{
  "error": "RecordInvalid",
  "description": "Record validation errors",
  "details": {
    "email": [
      {
        "description": "Email: monica@example.com is already being used by another user",
        "error": "DuplicateValue"
      }
    ]
  }
}"""
)


update_user_ok = create_user_result


user_identities = json.loads(
    """{
  "identities": [
    {
      "url": "https://example.zendesk.com/api/v2/users/1/identities/1.json",
      "id": 1,
      "user_id": 1,
      "type": "email",
      "value": "monica@example.com",
      "verified": true,
      "primary": true,
      "created_at": "2018-11-21T23:43:59Z",
      "updated_at": "2018-11-22T01:49:29Z",
      "undeliverable_count": 0,
      "deliverable_state": "deliverable"
    },
    {
      "url": "https://example.zendesk.com/api/v2/users/1/identities/2.json",
      "id": 2,
      "user_id": 1,
      "type": "email",
      "value": "monica2@example.com",
      "verified": true,
      "primary": true,
      "created_at": "2018-11-21T23:43:59Z",
      "updated_at": "2018-11-22T01:49:29Z",
      "undeliverable_count": 0,
      "deliverable_state": "deliverable"
    }
  ],
  "next_page": null,
  "previous_page": null,
  "count": 2
}"""
)

identity_make_primary = json.loads("""{}""")
