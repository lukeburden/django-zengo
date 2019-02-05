import json


new_ticket = json.loads(
    r"""{
  "ticket": {
    "url": "https://example.zendesk.com/api/v2/tickets/123.json",
    "id": 123,
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

ticket_with_comment = None
ticket_with_two_comments = None
ticket_with_changed_custom_fields = None

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

search_by_external_id_matches = json.loads(
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
